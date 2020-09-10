import os, sys, getopt,shutil,yaml

def usage(exitCode):
    str="""
                            .::::'`
                      : :::::'
                    .::::::.::::::::::
               ..:::::``::::::::
         ,cC'':::::: .:::::::::::::
         "?$$$$P'::::::::::::::::::::
            '':::::::::::::::::::::::
             .::::::::::: d$c`:`,c:::
             `::::::::::: $$$$, $$ :
            ,,,,```:::::: F "$'  ?::  ..:::::::::::..
          ,d$$$$$$$$$$c,` '  ?::   . :::::::::::::::::
        d$$$$$$$$$$$$$$$$$$$c$F,d$$F::::::::::::::::::
      d$$$$$$$$$$$F?$$$$$$$$$.$$$$$ ::::::::::::::::::.
    ,$$????$$$$$$$$$hccc-$$$$$$$$$$,::::::::::::::::',$
    '    4$$$$$$$$$$$$$$,"?$$$$$$$$$c`:::::::::::'',$"
         $$$"".$$$$$$$$$$$L`$$$$$$$$$$$bccc,ccc$$$$"
         "      ::: `?$$$$$$,??$$$$$$$$$$P"????"
                 :::: `$$$$$$
                  :::::`$d$
                    :: :?$$$::::
                  :::'.:4$$$'.:::
                 ::: ::4$$$$$ :`::
                 :::`: $$$$$$L::`:
                 `:::::?$$$$$$<: :
             ,,  ``  :::"$$$$ ::''
           $$??" =4- ,,`::"?::,c='? Lcdbc,
           c$$$$",$$$$$c"'  'dLd$$$$b,?$$$$
          ??$$$$,??$$$$$$     $$$$$c $ $$ J
          "?$$$$3`z$$$$P"     "?$$$$P" "      

Before building Security Controller Sensor, you must apply config in source code
by running genConfig.py

Example:
    > python genConfig.py --conf=config_prod.yaml --src_dir=. --build_dir=./target"""
    print(str)
    sys.exit(exitCode)


def applyConfig(srcName, dstName, conf):
    srcFile=open(srcName)
    dstFile=open(dstName,'w')

    line = srcFile.readline()
    while line:
        for key, value in conf.items():
            line=line.replace('#'+key+'#', value)
        dstFile.write(line)
        line = srcFile.readline()

    dstFile.close()
    srcFile.close()

def patchTree(src, dst, workList, conf):
    names = os.listdir(src)

    os.makedirs(dst)
    errors = []
    for name in names:
        srcName = src+'/'+name
        dstName = dst+'/'+name
        try:
            if srcName in workList['ignore']:
                continue
            elif os.path.isdir(srcName):
                patchTree(srcName, dstName,workList,conf)
            elif srcName in workList['configure']:
                print("Patch File %s" % dstName)
                applyConfig(srcName, dstName, conf)
            else:
                print("Copy %s -> %s" % (srcName,dstName))
                shutil.copy2(srcName, dstName)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error) as why:
            errors.append((srcName, dstName, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Exception as err:
            errors.extend(err.args[0])


def build_tree(srcDir, configFile, buildDir):
    if not os.path.exists(srcDir):
        raise Exception("Error, src_dir (%s) not found" % srcDir)

    if os.path.exists(buildDir):
        print("build_dir already exists, clean it")
        shutil.rmtree(buildDir, ignore_errors=True)

    with open(configFile, 'r') as yamlFile:
        config = yaml.safe_load(yamlFile)

    fileList = {'ignore': [srcDir+'/.idea', srcDir+'/venv'],
                'configure': [
                    srcDir+'/alarmController/config.h',
                    srcDir+'/domoticz/script_device_security2Warning.lua',
                    srcDir+'/domoticz/script_time_securityStatus.lua'
                    ]
                }
    patchTree(srcDir + "/alarmController", buildDir+"/alarmController",fileList,config)
    patchTree(srcDir + "/domoticz", buildDir+"/domoticz", fileList, config)

def main(argv):
    srcDir='.'
    configFile = ''
    buildDir = ''

    try:
      opts, args = getopt.getopt(argv,"hc:b:",["conf=","src_dir=","build_dir="])
    except getopt.GetoptError:
      usage(2)

    for opt, arg in opts:
      if opt == '-h':
         usage(0)
      elif opt in ("-s", "--src_dir"):
         srcDir = arg
      elif opt in ("-b", "--build_dir"):
         buildDir = arg
      elif opt in ("-c","--conf"):
          configFile = arg

    if configFile=='' or buildDir=='':
        print(usage)
        sys.exit()
    try:
        print("srcDir=[%s]  configFile=[%s] buildDir=[%s]" % (srcDir, configFile, buildDir))
        build_tree(srcDir, configFile, buildDir)
    except Exception as e:
        print(e)

if __name__ == "__main__":
   main(sys.argv[1:])

