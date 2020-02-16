# -*- coding: utf-8 -*-

import requests
#BS使用lxml解析器
from bs4 import BeautifulSoup
import time
import re
import urllib

import pymysql
# mysql数据库操作类
def getCon():
    '''获取操作数据库的curcor即游标，首先的建立连接，需要服务器地址，端口号，用户名，密码和数据库名'''
    conn = pymysql.connect(host="localhost", port=3306, user="root", password="123456", db="weibo",
                           charset="utf8mb4")
    return conn

def insertcrawler(user_id,user_name,wb_title,wb_content,wb_address,wb_date,wb_url,wb_forward,wb_comment,wb_like,keyword):
    '''向数据库中patentinfo表插入书本信息，patentinfo为PatentInfo类对象，包含专利基本信息'''
    sql = "insert into sina_feiyan(user_id,user_name,wb_title,wb_content,wb_address,wb_date,wb_url,wb_forward,wb_comment,wb_like,keyword) values(%s, %s, %s, %s, %s,%s,%s, %s, %s, %s,%s)"

    conn = getCon();
    if conn == None:
        return

    cursor = conn.cursor()
    cursor.execute(sql, (user_id,user_name,wb_title,wb_content,wb_address,wb_date,wb_url,wb_forward,wb_comment,wb_like,keyword))

    conn.commit()
    cursor.close()
    conn.close()


def readprovince():
    province_list = []
    with open('diqudaima.txt', 'r') as f:
        for line in f:
            province_list.append(list(line.strip('\n').split(':')))
        province_list = dict(province_list)
    print(province_list)
    return province_list


def readcity(code):
    city_dict = []
    with open("地区代码/%s.txt" % code, 'r') as f:
        for line in f:
            city_dict.append(list(line.strip('\n').split(':')))
    city_dict = dict(city_dict)
    print(city_dict)
    return city_dict


def find_content(soup, id):
    weibo_content = soup.find_all('p', attrs={"nick-name": id})
    if len(weibo_content) > 1:
        weibo_content = weibo_content[1].text
    else:
        weibo_content = weibo_content[0].text
    weibo_content = weibo_content.replace("收起全文d", "")
    weibo_content = weibo_content.replace("\n", "")
    weibo_content = weibo_content.strip()
    return weibo_content


def get_FCL(soup,type):
    string = soup.find(attrs={"action-type": "feed_list_"+type}).text
    string = re.findall("\d+", string)
    if len(string) == 0:
        number = 0
    else:
        number = int(string[0])
    return number


def get_theme(content):
    theme = re.findall(r'【(.*?)】', content)
    if len(theme) == 0:
        theme = ""
    else:
        theme = theme[0]
    return theme


def time_trans(times):
    time_list = re.findall(r'\d+', times)
    print(time_list)
    if len(time_list) == 4:
        new_time = '2020-' + str(time_list[0]) + '-' + str(time_list[1]) + '-' + str(time_list[2])
    else:
        new_time = str(time_list[0]) + '-' + str(time_list[1]) + '-' + str(time_list[2]) + '-' + str(time_list[3])
    return new_time


def getcontent(province_dict, topic, cookie, shar_time, end_time):
    for p in province_dict:
        #p为省份
        print('省份：',p)
        provence_code = province_dict[p]
        # provence_code = 12
        city_dict = readcity(provence_code)
        #c为城市
        for c in city_dict:
            print('城市：',c)
            city_code = city_dict[c]
            #city_code =
            cook = {"Cookie": " T_WM=%s" % cookie}  # 放入你的cookie信息。
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
            with open('weibo.txt', 'w', encoding='utf-8') as f:
                for pages in range(1, 51):
                    url = "https://s.weibo.com/weibo/%s&region=custom:%s:%s&typeall=1&suball=1&timescope=custom:%s:%s&Refer=g&page=%s" % \
                          (topic, provence_code, city_code, star_time, end_time, pages)
                    # 发送请求
                    response = requests.get(url, cookies=cook, headers=headers)
                    print(response)
                    html = response.text
                    soup = BeautifulSoup(html, 'lxml')
                    #---------------------检测是否没有结果---------------------------
                    result_flag = soup.find('div', class_="card card-no-result s-pt20b40")
                    if result_flag != None:
                        print("该地区下没有结果")
                        break
                    # ----------------------获取用户名列表----------------------------
                    id_list = re.findall(r'click:user_name">(.*?)</a>', html)
                    # -----------------获取用户界面网址列表---------------------
                    id_url_list = re.findall(r'<a href="(.*?)" class="name" target="_blank"', html)
                    # -----------------获取微博发送时间列表---------------------------
                    time_list = re.findall(r'click:wb_time">(.*?)</a>', html, re.S)
                    # -------------------获取转评赞列表----------------
                    FCLtag = soup.find_all('div', class_="card-act")

                    counter = 0
                    for id_name in id_list:
                        urls = id_url_list[counter]
                        user_id = urls[12:22]
                        print("用户ID：", user_id)
                        url = "http://m.weibo.cn/" + user_id
                        id_url = "https:%s" % id_url_list[counter]
                        # -------------------获取用户微博内容-------------
                        weibo_content = find_content(soup, id_name)
                        if len(weibo_content) > 800:
                            weibo_content = weibo_content[0:499]
                        # ------------------------获取时间---------------
                        times = time_list[counter]
                        times = times.replace(" ", "")
                        times = times.replace("\n", "")
                        # ----------------获取转评赞数------------------
                        try:
                            forward = get_FCL(FCLtag[counter], "forward")
                            comment = get_FCL(FCLtag[counter], "comment")
                            like = get_FCL(FCLtag[counter], "like")
                        except:
                            end_time = time_trans(times)
                            return end_time
                        # ---------------获取主题-----------------------
                        theme = get_theme(weibo_content)
                        # ----------------输出-------------------------
                        print("微博内容：", weibo_content)
                        print("发布时间：", times)
                        print("所在地：",c)
                        counter = counter + 1
                        # ----------------截取最后的微博时间-------------
                        if pages == 50 and counter == len(id_list):
                            end_time = time_trans(times)
                            print("重新爬取%s前的微博" % times)
                            return end_time
                        insertcrawler(user_id, id_name, theme, weibo_content, c, times, url, forward, comment, like,
                                     topic)
                        f.write('用户名：%s     微博内容：%s     地点：%s   时间：%s   转发数：%d  评论数：%d  点赞数：%d  主题：%s\n' % (
                        id_name, weibo_content, c, times, forward, comment, like, theme))

                    time.sleep(30)


if __name__ == '__main__':
    provinve_dict = readprovince()
    topic = '新型肺炎'
    cookie = 'SINAGLOBAL=7287819551767.784.1557887876330; un=13247111953; wvr=6; UOR=www.baidu.com,weibo.com,www.baidu.com; Ugrow-G0=9ec894e3c5cc0435786b4ee8ec8a55cc; login_sid_t=8360a29f7e8990905a284b41eeeacff0; cross_origin_proto=SSL; YF-V5-G0=9903d059c95dd34f9204f222e5a596b8; WBStorage=42212210b087ca50|undefined; _s_tentry=passport.weibo.com; wb_view_log=1536*8641.25; Apache=730209885103.5565.1581502007915; ULV=1581502007924:71:17:2:730209885103.5565.1581502007915:1581413036426; crossidccode=CODE-yf-1J1OV8-45EOsg-Ewo8F8iNFw4lb3saf2f69; ALF=1613038028; SSOLoginState=1581502029; SCF=Al7k1l1TF3MOjGReJVQozKt0EtQhgEFmRouWp5K1auDUf5QCCcDqB6T-O_JLO0v91jPshCPc5vF0ZTsZZAnELiI.; SUB=_2A25zR74dDeThGeFM61AY-SrNzj2IHXVQNKjVrDV8PUNbmtANLVXakW9NQOcALRoxBWTHS0tJfrZK3JhzebyAQMMX; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWFSadMyrx9E5qDEy2THT4F5JpX5KzhUgL.FoMEehz41KBpSK22dJLoIE.LxK-LBKqL1hzLxK.LBo.LB.qLxK-LB.BL1KzLxKqL1--L1KMX1KeN1Btt; SUHB=0D-VGpwXKFIsvq'
        # 'SINAGLOBAL=7287819551767.784.1557887876330; un=13247111953; Ugrow-G0=5c7144e56a57a456abed1d1511ad79e8; YF-V5-G0=9903d059c95dd34f9204f222e5a596b8; wb_view_log_5199677611=1536*8641.25; _s_tentry=weibo.com; Apache=5173244068468.921.1580542907166; ULV=1580542907341:55:1:5:5173244068468.921.1580542907166:1580454296840; webim_unReadCount=%7B%22time%22%3A1580550187062%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22allcountNum%22%3A69%2C%22msgbox%22%3A0%7D; YF-Page-G0=f0aa2e6d566ccd1c288fae19df01df56|1580550186|1580550159; login_sid_t=d749df1d89555f0f6f0cb722e7d139b1; cross_origin_proto=SSL; WBStorage=42212210b087ca50|undefined; wb_view_log=1536*8641.25; crossidccode=CODE-yf-1IXPjc-29rKYx-Eet8cbgw7kMOuYI7abd64; UOR=www.baidu.com,weibo.com,login.sina.com.cn; ALF=1612086211; SSOLoginState=1580550212; SCF=Al7k1l1TF3MOjGReJVQozKt0EtQhgEFmRouWp5K1auDUfWdDwhyenMrVbOw2hSVMAOqU9I4LqEzaB099jJCxiSE.; SUB=_2A25zMTgUDeThGeFM61AY-SrNzj2IHXVQRy7crDV8PUNbmtAfLRDhkW9NQOcALQbfSdDCLkZGLf57y0ae6O80NSI_; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWFSadMyrx9E5qDEy2THT4F5JpX5KzhUgL.FoMEehz41KBpSK22dJLoIE.LxK-LBKqL1hzLxK.LBo.LB.qLxK-LB.BL1KzLxKqL1--L1KMX1KeN1Btt; SUHB=0nl-plVEEuwq0X; wvr=6'
        # 'SINAGLOBAL=7287819551767.784.1557887876330; UOR=www.baidu.com,weibo.com,www.baidu.com; login_sid_t=cc2527870d5c0a1c287c28aa5be899f4; cross_origin_proto=SSL; Ugrow-G0=5c7144e56a57a456abed1d1511ad79e8; YF-V5-G0=e8fcb05084037bcfa915f5897007cb4d; WBStorage=42212210b087ca50|undefined; wb_view_log=1536*8641.25; _s_tentry=www.baidu.com; Apache=5692157745401.491.1580370453399; ULV=1580370453430:51:2:1:5692157745401.491.1580370453399:1578640950469; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFCe7PweK6mr43Y-w1CYdsG5JpX5K2hUgL.Fo-p1K.cS0MceK22dJLoIEUQqgRLxKqL1K.L1KMLxKqL1heL1h-LxKnL1hBL1h.LxKnL1hBL1h.t; ALF=1611906459; SSOLoginState=1580370460; SCF=Al7k1l1TF3MOjGReJVQozKt0EtQhgEFmRouWp5K1auDURxJLAcXqdUb5NBraOrE-hL3upvfz1465SFfiBZON1sM.; SUB=_2A25zNvpMDeRhGeNP4lsX9ynKyj2IHXVQQmyErDV8PUNbmtANLWv7kW9NTllDXBMj8AN14EVp9m_daP-6pMQ-xe1I; SUHB=0P1M176oWS7-ar; un=13247111953; wvr=6; YF-Page-G0=bf52586d49155798180a63302f873b5e|1580370475|1580370475; wb_view_log_5199677611=1536*8641.25'
        # 'SINAGLOBAL=7287819551767.784.1557887876330; httpsupgrade_ab=SSL; wvr=6; UOR=www.baidu.com,weibo.com,www.baidu.com; Ugrow-G0=589da022062e21d675f389ce54f2eae7; login_sid_t=9c19c95a63eb7b93d772821e3d1ceb4d; cross_origin_proto=SSL; YF-V5-G0=70942dbd611eb265972add7bc1c85888; WBStorage=384d9091c43a87a5|undefined; wb_view_log=1920*10801; _s_tentry=passport.weibo.com; Apache=1455392951175.274.1569126887260; ULV=1569126887330:41:13:1:1455392951175.274.1569126887260:1569053626567; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFCe7PweK6mr43Y-w1CYdsG5JpX5K2hUgL.Fo-p1K.cS0MceK22dJLoIEUQqgRLxKqL1K.L1KMLxKqL1heL1h-LxKnL1hBL1h.LxKnL1hBL1h.t; ALF=1600662894; SSOLoginState=1569126895; SCF=Al7k1l1TF3MOjGReJVQozKt0EtQhgEFmRouWp5K1auDU5w1JaqchxlAXQOUdA9Sc6zVEGnf2mkIyaYs2eeKgV4w.; SUB=_2A25wgom_DeRhGeNP4lsX9ynKyj2IHXVT-fx3rDV8PUNbmtBeLWjekW9NTllDXEGhPn31PpUTEFjVlBzBvJmZrmly; SUHB=0OMkDlyAmEi_Bc; un=13247111953; wb_view_log_5199677611=1920*10801; YF-Page-G0=e57fcdc279d2f9295059776dec6d0214|1569126900|1569126900; webim_unReadCount=%7B%22time%22%3A1569126901373%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22allcountNum%22%3A61%2C%22msgbox%22%3A0%7D'
                # 'ALF=1571815232; SCF=Ajtw88hr_Zd5yc6t3zztEelUTR3RLv8oVzUjDpo2fX8ZQKKGdr0pvWyFxrN78L8OUeJScpRyridtD3q8glwPlBc.; SUB=_2A25wjfPSDeRhGeBK6lcV-C_JyTyIHXVQcZ2arDV6PUJbktAKLVKmkW1NR_4Ny3W5tksrF593LRT706HGUoTYJ0kw; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5IRYcfGo0MziHdcuMrfncq5JpX5K-hUgL.FoqXeK-X1h2feo52dJLoI79Kdc40dc2t; SUHB=0pHx9xlM8c0hN9; SSOLoginState=1569293186; MLOGIN=1; _T_WM=48991577496; XSRF-TOKEN=35db35; WEIBOCN_FROM=1110006030; M_WEIBOCN_PARAMS=luicode%3D20000174%26uicode%3D20000174'
        #'SINAGLOBAL=6165869682540.818.1557314119433; un=18742505841; un=18742505841; wvr=6; _ga=GA1.2.1798755396.1568986450; _gid=GA1.2.939219373.1568986450; __gads=ID=35d26344fe20c1ef:T=1568986449:S=ALNI_MaDBAD1aZoGscJTsakQpJ5vBcBCJg; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5vLA56DOVwSwsd53CW32Zw5JpX5KMhUgL.FoMES0BReo-Xeo.2dJLoI7pDdg8EdciaUhz7eK.t; ALF=1600570805; SSOLoginState=1569034806; SCF=AodvKWB66Z89guvjZsxQVkVBzmDIHMeXbL-qZWmS5dIMR4rxtT_nCPucjhpGmG4tapE-RLLw9lmt9BbhSrqBhc4.; SUB=_2A25wgeJmDeRhGeFM7FYZ8ivIyTWIHXVT91SurDV8PUNbmtANLUbfkW9NQKI-eCbhT_j3O0bnF4xKKBUKBjpVsBTR; SUHB=0LcSYxm5bfq_N1; _s_tentry=login.sina.com.cn; UOR=,,login.sina.com.cn; Apache=7209978587258.692.1569034810259; ULV=1569034810307:27:8:4:7209978587258.692.1569034810259:1568985546767; webim_unReadCount=%7B%22time%22%3A1569035408156%2C%22dm_pub_total%22%3A1%2C%22chat_group_client%22%3A0%2C%22allcountNum%22%3A31%2C%22msgbox%22%3A0%7D'
    end_time = '2020-01-29 08'
    star_time = '2019-12-01'
    while True:
        end_time = getcontent(provinve_dict, topic, cookie, star_time, end_time)
