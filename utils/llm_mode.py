import asyncio
import datetime

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion

from config import USE_AZURE


class SemanticKernel:
    def __init__(self):
        self.kernel = sk.Kernel()
        self.score_function = None
        if USE_AZURE is True:
            deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
            self.kernel.add_chat_service("dv", AzureChatCompletion(deployment, endpoint, api_key))
        else:
            api_key, org_id = sk.openai_settings_from_dot_env()
            self.kernel.add_chat_service("dv", OpenAIChatCompletion("gpt-3.5-turbo", api_key))

        self.prompt_extract_parts = ""
        self.prompt_score = ""
        self.prompt_extract_news = ""
        self.read_prompt()

    def read_prompt(self):
        with open("./prompt/prompt_ranking.txt", "r", encoding="utf-8") as file:
            self.prompt_score = file.read()
        with open("./prompt/prompt_extract_parts.txt", "r", encoding="utf-8") as file:
            self.prompt_extract_parts = file.read()
        with open("./prompt/prompt_extract_news.txt", "r", encoding="utf-8") as file:
            self.prompt_extract_news = file.read()

    def extract_html(self, web_content: str):
        content_copy = web_content
        contents = []
        ext = ""
        while len(content_copy) > 3000:
            contents.append(content_copy[:3000])
            content_copy = content_copy[3000:]
        contents.append(content_copy)
        extract_part_function = self.kernel.create_semantic_function(self.prompt_extract_parts, max_tokens=500,
                                                                     temperature=0.0,
                                                                     top_p=0.0)
        for i, content in enumerate(contents):
            ext += str(extract_part_function(content))
            print(f"新闻内容分段处理已完成 - {i + 1}/{len(contents)}")
            ext += "\n"
        print("新闻内容提取完成，总结中......")
        extract_function = self.kernel.create_semantic_function(self.prompt_extract_news,
                                                                max_tokens=1000, temperature=0.8, top_p=0.5)
        ans = extract_function(ext)
        print("新闻内容总结完成，评分中......")
        return str(ans)

    def score_news(self, news_content: str, temperature: float, company_name: str, term: int, top_p=0.5):
        self.score_function = self.kernel.create_semantic_function(
            self.prompt_score, max_tokens=1000, temperature=temperature, top_p=top_p)
        context = self.kernel.create_new_context()
        context["company_name"] = company_name
        context["term"] = str(term)
        context["date_time"] = datetime.datetime.now().strftime("%Y-%m-%d")
        context["input"] = str(news_content)
        score = asyncio.run(self.score_async_function(context))
        return score

    async def score_async_function(self, context):
        answer = await self.score_function.invoke_async(context=context)
        print("该条新闻评分完成!")
        return answer

    def sk_test(self, content, max_tokens=1000, temperature=0.0, top_p=0.0):
        test = self.kernel.create_semantic_function(
            content, max_tokens=max_tokens, temperature=temperature, top_p=top_p)
        return str(test())
