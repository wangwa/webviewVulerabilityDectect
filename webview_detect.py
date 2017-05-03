# -*- coding: utf-8 -*-
__author__ = 'peter.liang'

##############################################################################
# this script is to detect WebView Component Vulnerability in Android APP. test for win pycharm
#modify by peter change to master
###############################################################################

import os
import re
import sys
import datetime
import time
import commands
import traceback
import shutil


BASE_LEVEL = 0
DEBUG = BASE_LEVEL + 1
ERROR = BASE_LEVEL + 2

LOGFILE = os.path.join(os.curdir, "log.log")

MANIFESTFILENAME = "AndroidManifest.xml"

SETMETHOD_SPECIAL_FOMMAT = "Landroid/webkit/WebSettings;->setAllowUniversalAccessFromFileURLs"
WEBVIEW_COMP_FOMMAT = "Landroid/webkit/WebView"

DEBUG_LEVEL = ERROR

def log(msg, level=ERROR):
    if level >= DEBUG_LEVEL:
        print(msg)
        x = time.localtime(time.time())
        cmd = "echo Date%s   %s >> %s" % (time.strftime('%Y-%m-%d %H:%M:%S',x), msg, LOGFILE)
        os.system(cmd)

def getManifestInfo(manifestFilePath):
    pkgName = ""
    androidVer = ""
    sdkversion = ""

    log("In getManifestInfo. manifest:%s" % manifestFilePath, DEBUG)

    cmd = "cat %s |grep \"xmlns:android\"" % manifestFilePath

    ret, output = commands.getstatusoutput(cmd)
    if ret != 0 or not output.strip():
        log("command:%s fail.output:%s" % (cmd, output))
        return "", "", ""

    listStr = output.split()
    if len(listStr) < 1:
        log("Invalid manifest file:%s fail.output:%s" % (cmd, output))
        return "", "", ""

    for tmp in listStr:
        if tmp.strip().startswith("package="):
            pkgName = tmp.split("=")[1].strip(">").strip("\"").strip("\'")

        if tmp.strip().startswith("platformBuildVersionCode="):
            sdkversion = tmp.split("=")[1].strip(">").strip("\"").strip("\'")

        if tmp.strip().startswith("platformBuildVersionName="):
            androidVer = tmp.split("=")[1].strip(">").strip("\"").strip("\'")

    log("Leaving getManifestInfo. manifest:%s" % manifestFilePath, DEBUG)

    return pkgName, androidVer, sdkversion

def checkSetTrue(smaliFilePath):
    """
        smalifile中已经有调用setAllowUniversalAccessFromFileURLs(Bool)，判断设置的值是不是true
    :param smaliFilePath:
    :return:
    """

    listLine = []
    f = None

    log("In checkSetTrue. manifest:%s" % smaliFilePath, DEBUG)

    try:
        f = open(smaliFilePath, 'r')
        while True:
            line = f.readline()
            if line is None or line == "":
                break
            listLine.append(line)
    except:
        log("Read file:%s fail.errinfo:%s" % (smaliFilePath, traceback.format_exc()))
        exit(1)
    finally:
        if f:
            f.close()

    try:
        #遍历文件内容
        listLine.reverse()
        name = None
        for line in listLine:
            strTmp = re.search(SETMETHOD_SPECIAL_FOMMAT, line)
            if strTmp is None and name is None:
                continue

            if strTmp is not None:
                #查找参数的寄存器名字
                idxPos1 = line.index("{")
                idxPos2 = line.index("}")
                strTmp = line[idxPos1+1:idxPos2]
                name = strTmp.split(",")[1].strip()
            elif name is not None:
                #查找寄存器存放的值
                strTmp2 = re.search("const\/4 %s" % name, line)
                if strTmp2 is None:
                    continue

                strTmp2 = line.split(",")[1].strip()

                #寄存器皴法0x1为true，0x0为false
                if strTmp2 == "0x1":
                    return True

                #找到寄存器存放的值后，清空寄存器的名字。
                name = None
    except:
        log(traceback.format_exc())
        exit(1)

    log("Leaving checkSetTrue. manifest:%s" % smaliFilePath, DEBUG)

    return False


def apkfileDetect(strFilePath):

    log("In apkfileDetect. apk:%s" % strFilePath, DEBUG)

    if not os.path.exists(strFilePath):
        log("file %s not exist." % strFilePath)
        exit(1)

    pwdpath = os.path.dirname(os.path.realpath(__file__))
    rootpath = os.path.join(pwdpath, "roottmp")
    if os.path.exists(rootpath):
        cmd = "rm -rf %s" % rootpath
        os.system(cmd)

    os.mkdir(rootpath)
    shutil.copy(strFilePath, rootpath)
    apkname = os.path.basename(strFilePath)
    dstpath = os.path.join(rootpath, apkname)

    if not os.path.exists(dstpath):
        log("copy file %s to %s fail." % (strFilePath, rootpath))
        exit(1)

    decodepath = os.path.join(rootpath, "apktmp")
    cmd = "apktool d %s -o %s" % (dstpath, decodepath)
    ret, output = commands.getstatusoutput(cmd)
    if ret != 0:
        log("decode file %s fail." % dstpath)
        exit(1)

    manifestFilePath = os.path.join(decodepath, MANIFESTFILENAME)
    smaliRootPath = os.path.join(decodepath, "smali")

    pkgName, androidVer, sdkVersion = getManifestInfo(manifestFilePath)

    if not pkgName:
        log("Get package name fail from file:%s." % manifestFilePath)
        exit(1)

    if not androidVer:
        log("Get Android Version fail from file:%s." % manifestFilePath)
        exit(1)

    if not sdkVersion:
        log("Get SDK Version fail from file:%s." % manifestFilePath)
        exit(1)

    log("apkfileDetect. pkgName:%s, androidVer:%s, sdkVersion:%s." % (pkgName,androidVer,sdkVersion), DEBUG)

    #遍历所有的smali文件，检查是否有WebView的漏洞。
    smaliFilesPath = os.path.join(smaliRootPath, pkgName.replace(".", "/"))

    hasVulnerability = False
    for root, dirs, files in os.walk(smaliFilesPath):
        if len(files) < 1:
            continue

        #解析smali文件内容，是否有Webview控件，如果有，判断
        #运行在Android 4.0 及以前： setAllowUniversalAccessFromFileURLs(Bool)参数未设为false
	    #运行在Android 4.1 及以后：
		#    1） 应用的manifest的android:targetSdkVersion < 16 时， setAllowUniversalAccessFromFileURLs(Bool)参数未设为false 或者
		#    2） 应用的manifest的android:targetSdkVersion >= 16 时， setAllowUniversalAccessFromFileURLs(Bool)参数设为true
        for file in files:
            filePath = os.path.join(root, file)
            cmd = "cat %s |grep %s" % (filePath, WEBVIEW_COMP_FOMMAT)
            ret, output = commands.getstatusoutput(cmd)
            if ret != 0:
                log("apkfileDetect. not find webview file:%s, ret:%s." % (file, ret), DEBUG)
                continue

            if output.strip() == "":
                #未使用webview控件
                log("apkfileDetect. not find webview file:%s." % file, DEBUG)
                continue

            log("apkfileDetect. find webview file:%s." % file, DEBUG)

            if androidVer <= "4.0":
                cmd  = "cat %s |grep %s" % (filePath, SETMETHOD_SPECIAL_FOMMAT)
                ret, output = commands.getstatusoutput(cmd)

                log("apkfileDetect. android ver less than 4.0", DEBUG)

                if ret != 0 or output.strip() == "" or checkSetTrue(filePath):
                    #未调用setAllowUniversalAccessFromFileURLs接口设置 或者 调用setAllowUniversalAccessFromFileURLs接口设置True
                    hasVulnerability = True
                    break

            elif androidVer >= "4.1":
                cmd  = "cat %s |grep %s" % (filePath, SETMETHOD_SPECIAL_FOMMAT)
                ret, output = commands.getstatusoutput(cmd)
                if sdkVersion < "16":
                    log("apkfileDetect. android ver more than 4.0, sdk version less than 16", DEBUG)
                    if ret != 0 or output.strip() == "" or checkSetTrue(filePath):
                        #未调用setAllowUniversalAccessFromFileURLs接口设置 或者 调用setAllowUniversalAccessFromFileURLs接口设置True
                        hasVulnerability = True
                        break
                elif sdkVersion >= "16":
                    log("apkfileDetect. android ver more than 4.0, sdk version more than 16", DEBUG)
                    if output.strip() != "" and checkSetTrue(filePath):
                        #调用setAllowUniversalAccessFromFileURLs接口设置True
                        hasVulnerability = True
                        break
                else:
                    log("Invalid sdk version:%s" % sdkVersion)
                    continue
            else:
                pass

        if hasVulnerability:
            break

    log("Leaving apkfileDetect. apk:%s" % strFilePath, DEBUG)

    return hasVulnerability


if __name__ == "__main__":
    if len(sys.argv) < 1:
        log("Pls input absolute path of apk file.")
        exit(1)
    else:
        filepath = sys.argv[1]
        log("Begin scan file:%s" % filepath)
        try:
            if apkfileDetect(filepath):
                log("There is WebView Vulnerability in ApkFile:%s" % filepath)
            else:
                log("There is not WebView Vulnerability in ApkFile:%s" % filepath)
        except:
            log("Detect Err:%s" % traceback.format_exc())
            exit(1)
        log("Success scanned file:%s" % filepath)




