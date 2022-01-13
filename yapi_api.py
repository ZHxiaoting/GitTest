# -*- coding: utf-8 -*-
# @Time    : 2021/10/22 14:30 下午
# @Author  : ys
'''
#   需要安装依赖库
#   pip install requests
#   pip install BeautifulSoup
'''

import os
import re
import smtplib
import time
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bs4 import BeautifulSoup
import requests

project_id="27"#项目id
token="2207d52cf8ec9e6e12cee5a2abc1319d06cf5e06690c51d3442ce5d2bc75691f"
env="Saas_xiaoan_dev_13241471603"
#env_27=SaaS小安-后台管理测试环境-13241471603

#测试集合
case_col={
    999:"设备管理基本业务流程验证",
    639:"设备分组基本业务流程验证",
    795:"技能配置基本操作",
    519:"车牌(组)基本操作",
    #525:"人脸(组)基本操作",
    849:"车牌(组)应用到技能业务模拟",
    #837:"人脸(组)应用到技能业务模拟",
   # 1100:"图像事件上报数据集",
    # 861:"account平台企业成功基本业务流程验证"

}

base_url="http://10.216.80.220:3000/api/open/run_auto_test?" \
         "id={}&token={}&env_{}={}&mode=html&email=false&download=false"

#yapi选择测试环境时会同步携带配置信息
# headers={
#     "Cookie":"__guid=134303092.631179075594695700.1634812313969.319; Q=u%3D360H2604431865%26n%3D%26le%3D%26m%3DZGZlWGWOWGWOWGWOWGWOWGWOAwNm%26qid%3D2604431865%26im%3D1_t012fd29a285d296bb0%26src%3Dpcw_monitorzyun%26t%3D1; T=s%3D15bfcb63a701a6954afbd5cbd3278cde%26t%3D1634812317%26lm%3D%26lf%3D2%26sk%3D05a14e88cfadc5d6fb309c29f66e1a1b%26mt%3D1634812317%26rc%3D%26v%3D2.0%26a%3D1; test_cookie_enable=null"}
#

def cases_summary(file_name):
    '''
    测试详情统计
    '''
    with open(file_name,'rb') as f:
        #提取执行结果
        file_line=f.read()
        soup = BeautifulSoup(file_line, "html.parser")
        summary = soup.find_all('div', class_='summary')
        
        if( len(summary)!= len(case_col) ):
            print("存在部分测试集遗留情况，请核实！")
            return False

        sum_result = []
        for i in range(len(summary)):
            cont_right_list = soup.select('body div.content-right')
            cases_group = cont_right_list[i].select('h1')[0].string
            sum_result.append(one_summary(summary[i], cases_group))
        print(sum_result)

        #测试全量统计
        result=""
        total_num = 0
        pass_num = 0
        fail_num = 0
        run_time = 0
        for i_summ in sum_result:
            total_num += i_summ['total_num']
            pass_num += i_summ['pass_num']
            fail_num += i_summ['fail_num']
            run_time += float(re.findall(r"\d+\.?\d*", i_summ['run_time'])[0])

        total_summary= "<body>本轮接口自动运行<b>总用例数：%d(通过：%d,  失败：%d)</b>    总耗时:%0.2fs    相关用例集执行情况参见下文！<br></body>" % (total_num, pass_num, fail_num, run_time)
        result+=total_summary

        #测试集详情统计
        for i_summ in sum_result:
            cases_group = re.findall('(?<=【).*(?=】)',i_summ['case_col'])[0]
            total_num =i_summ['total_num']
            pass_num = i_summ['pass_num']
            fail_num = i_summ['fail_num']
            run_time = i_summ['run_time']

            cases_summary = "<body><blockquote><b>%s</b>:    总用例数：%d(通过：%d,  失败：%d)    运行总耗时:%s.<br></blockquote></body>" % (cases_group,total_num, pass_num, fail_num, run_time)
            result+=cases_summary
        result+="<br>详情请参见附件测试报告！<br><br> 祝好！<br>"
        print(result)
        return result



def one_summary(summary,cases_group):
    result = {
        'case_col':cases_group,
        'total_num': 0,
        'pass_num': 0,
        'fail_num': 0,
        'run_time': "0.0s"
    }
    result['total_num']=int(re.findall('\d+', str(re.findall('一共(.*)测试用例', str(summary))[0]))[0])
    # p1 = re.compile(r'[(](.*?)[)]', re.S)
    result['run_time'] = re.findall(re.compile(r'[(](.*?)[)]', re.S), str(summary))[0]
    result['pass_num'] = result['total_num']
    result['fail_num'] = 0
    if (-1 != str(summary).find("未通过")):
        # 存在失败用例
        result['fail_num']  = int(re.findall('验证通过，(.*)个未通过', str(summary))[0])
        result['pass_num'] = result['total_num'] -  result['fail_num']
    # result = "本轮接口运行总用例数：%d(通过数：%d,  失败数：%d).\n  运行总耗时:%s.\n  详情请参见附件测试报告！" % (total_num, pass_num, fail_num, run_time)
    return result

def run_api():

    report_name = ""
    try:
        report_name = "report_{}.html".format(time.strftime("%Y%m%d%H%M%S"))
        with open(report_name,'w', encoding='utf-8') as fh:
            t1 = datetime.now()
            for col_id in case_col:
                url = base_url.format(col_id,token,project_id,env)
                print("访问地址：%s" %(url))
                response = requests.get(url)
                contents = response.text
                # 添加用例集信息
                index = contents.find("YApi 测试报告")+len("YApi 测试报告")
                # print("contents[0:index]是%s：" % (contents[0:index]))
                # print("contents[index:]是%s：" % (contents[index:]))
                new_contents = contents[0:index]+"【用例集：%s-%s】"%(col_id,case_col[col_id])
                new_contents+=contents[index:]
                fh.write(new_contents)
                t2 = datetime.now()
                st = (t2 - t1).seconds
                t1=t2
                print("用例集【%s-%s】 执行耗时: %s s" % (col_id, case_col[col_id], st))
        
    except Exception as e:
        print("接口自动化执行报错，具体用例集：【%s-%s】,详情参见：" %(col_id,case_col[col_id],str(e)))
    finally:
        print("测试报告名：%s" % (report_name))
        return report_name

def send_email(newfile):
    f=open(newfile,'rb')
    mail_body=f.read()
    f.close()
    mail_host = 'mail.corp.qihoo.net'
    mail_user = 'yaoshuang@360.cn'
    mail_pass = 'Z6PhCZmKwVBjb3$'
    sender = 'yaoshuang@360.cn'
    receiver = ['yaoshuang@360.cn']
    title = '【监控SaaS-小安】YApi接口流水线执行测试报告'

    msg = MIMEMultipart('mixed')
    text=cases_summary(newfile)       #提取统计数据
    msg.attach(MIMEText(text,'html','utf-8'))

    msg_html = MIMEText(mail_body, 'html', 'utf-8')
    msg_html["Content-Disposition"] = 'attachment; filename="TestReport.html"'
    msg.attach(msg_html)

    msg['From'] = '姚双<yaoshuang@360.cn>'
    msg['To'] = ";".join(receiver)
    msg['Subject'] = Header(title, 'utf-8')

    smtp = smtplib.SMTP(host=mail_host,port=587)
    smtp.connect(mail_host, 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.login(mail_user, mail_pass)
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()

if __name__ == '__main__':
    # dir = os.path.dirname(os.path.abspath(__file__))
    # file = dir+"\\report_20211025165345.html"
    # cases_summary(file)
    # test(file)
    report_file = run_api()
    send_email(report_file)
