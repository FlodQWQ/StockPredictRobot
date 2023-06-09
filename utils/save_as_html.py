from datetime import datetime

from jinja2 import Environment, FileSystemLoader


def save_html(info: dict, origin: dict, path: str):
    try:
        table_body = []
        cnt = 1
        for key, value in origin.items():
            tmp = {
                "number": cnt,
                "title": value['title'],
                "url": value['url'],
                "score": value['score'],
                "content": value['content'],
                "reason": value['reason'],
                "date": value['date']
            }
            table_body.append(tmp)
            cnt += 1

        env = Environment(loader=FileSystemLoader('./utils'))
        template = env.get_template('template.html')
        with open(path, 'w+', encoding="utf-8") as file:
            html_content = template.render(
                body=table_body,
                company_name=info["company_name"],
                stock_code=info["stock_code"],
                total_score=info["total_score"],
                predict_result=info["predict_result"],
                generate_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            file.write(html_content)
        return f"成功保存到: {path}"
    except:
        return "保存失败!"
