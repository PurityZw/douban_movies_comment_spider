import requests_html
# py3 实现
if __name__ == '__main__':
    request = requests_html.HTMLSession()
    response = request.get('https://movie.douban.com/top250')
    result = response.html.xpath("//*[@id='content']/div/div[1]/ol/li")
    for i in result:
        name = i.xpath("//span[@class='title'][1]/text()")
        print(name)
