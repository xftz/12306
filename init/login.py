# -*- coding=utf-8 -*-
import copy
import time
from collections import OrderedDict
from time import sleep
import TickerConfig
from inter.GetPassCodeNewOrderAndLogin import getPassCodeNewOrderAndLogin1
from inter.GetRandCode import getRandCode
from inter.LoginAysnSuggest import loginAysnSuggest
from inter.LoginConf import loginConf
from myException.UserPasswordException import UserPasswordException

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

# 去除浏览器识别
option = ChromeOptions()
option.add_experimental_option('excludeSwitches', ['enable-automation'])
option.add_argument('--disable-blink-features=AutomationControlled')


class GoLogin:
    def __init__(self, session, is_auto_code, auto_code_type):
        self.session = session
        self.randCode = ""
        self.is_auto_code = is_auto_code
        self.auto_code_type = auto_code_type

    def auth(self):
        """
        :return:
        """
        self.session.httpClint.send(self.session.urls["loginInitCdn1"])
        uamtkStaticUrl = self.session.urls["uamtk-static"]
        uamtkStaticData = {"appid": "otn"}
        return self.session.httpClint.send(uamtkStaticUrl, uamtkStaticData)

    def codeCheck(self):
        """
        验证码校验
        :return:
        """
        codeCheckUrl = copy.deepcopy(self.session.urls["codeCheck1"])
        codeCheckUrl["req_url"] = codeCheckUrl["req_url"].format(self.randCode, int(time.time() * 1000))
        fresult = self.session.httpClint.send(codeCheckUrl)
        if not isinstance(fresult, str):
            print("登录失败")
            return
        fresult = eval(fresult.split("(")[1].split(")")[0])
        if "result_code" in fresult and fresult["result_code"] == "4":
            print(u"验证码通过,开始登录..")
            return True
        else:
            if "result_message" in fresult:
                print(fresult["result_message"])
            sleep(1)
            self.session.httpClint.del_cookies()

    def baseLogin(self, user, passwd):
        """
        登录过程
        :param user:
        :param passwd:
        :return: 权限校验码
        """
        logurl = self.session.urls["login"]

        loginData = OrderedDict()
        loginData["username"] = user,
        loginData["password"] = passwd,
        loginData["appid"] = "otn",
        loginData["answer"] = self.randCode,

        tresult = self.session.httpClint.send(logurl, loginData)
        if 'result_code' in tresult and tresult["result_code"] == 0:
            print(u"登录成功")
            tk = self.auth()
            if "newapptk" in tk and tk["newapptk"]:
                return tk["newapptk"]
            else:
                return False
        elif 'result_message' in tresult and tresult['result_message']:
            messages = tresult['result_message']
            if messages.find(u"密码输入错误") is not -1:
                raise UserPasswordException("{0}".format(messages))
            else:
                print(u"登录失败: {0}".format(messages))
                print(u"尝试重新登陆")
                return False
        else:
            return False

    def getUserName(self, uamtk):
        """
        登录成功后,显示用户名
        :return:
        """
        if not uamtk:
            return u"权限校验码不能为空"
        else:
            uamauthclientUrl = self.session.urls["uamauthclient"]
            data = {"tk": uamtk}
            uamauthclientResult = self.session.httpClint.send(uamauthclientUrl, data)
            if uamauthclientResult:
                if "result_code" in uamauthclientResult and uamauthclientResult["result_code"] == 0:
                    print(u"欢迎 {} 登录".format(uamauthclientResult["username"]))
                    return True
                else:
                    return False
            else:
                self.session.httpClint.send(uamauthclientUrl, data)
                url = self.session.urls["getUserInfo"]
                self.session.httpClint.send(url)

    def go_login(self):
        """
        登陆
        :param user: 账户名
        :param passwd: 密码
        :return:
        """
        user, passwd = TickerConfig.USER, TickerConfig.PWD
        if not user or not passwd:
            raise UserPasswordException(u"温馨提示: 用户名或者密码为空，请仔细检查")
        login_num = 0
        while True:
            if loginConf(self.session):
                # result = getPassCodeNewOrderAndLogin1(session=self.session, imgType="login")
                # if not result:
                #     continue
                # self.randCode = getRandCode(self.is_auto_code, self.auto_code_type, result)
                # print(self.randCode)
                # login_num += 1
                # self.auth()
                # if self.codeCheck():
                #     uamtk = self.baseLogin(user, passwd)
                #     if uamtk:
                #         self.getUserName(uamtk)
                #         break
                driver = webdriver.Chrome(
                    "C:\\Users\\22950\\.cache\\selenium\\chromedriver\\win32\\110.0.5481.77\\chromedriver.exe",
                    options=option)
                driver.implicitly_wait(10)
                driver.maximize_window()
                driver.get("https://kyfw.12306.cn/otn/resources/login.html")

                driver.find_element(By.XPATH,
                                    '//*[@id="J-userName"]').send_keys(user)
                driver.find_element(By.XPATH,
                                    '//*[@id="J-password"]').send_keys(passwd)
                driver.find_element(By.XPATH,
                                    '//*[@id="J-login"]').click()


                # 找滑块
                ele = driver.find_element(By.XPATH, '//*[@id="nc_1_n1z"]')

                # 使用action操作鼠标
                action = ActionChains(driver)
                # 鼠标移动到元素
                action.move_to_element(ele)
                # 按住鼠标
                action.click_and_hold(ele)
                # 拖动300个水平像素
                action.move_by_offset(300,0)
                # 放开鼠标
                action.release()
                # 一定要让上面的操作执行
                action.perform()

                time.sleep(3)

                if driver.get_cookie(name='tk'):
                    result = driver.get_cookie(name='tk')["value"]
                    self.getUserName(result)
                    break
                else:
                    continue
            else:
                loginAysnSuggest(self.session, username=user, password=passwd)
                login_num += 1
                break