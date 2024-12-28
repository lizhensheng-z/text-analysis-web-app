import streamlit as st
import requests
from bs4 import BeautifulSoup
import jieba
from collections import Counter
from pyecharts import options as opts
from pyecharts.charts import WordCloud, Bar, Pie, Scatter, Line, Radar, Kline
from streamlit.components.v1 import html

# 页面标题
st.title("中文文章分析与词频可视化")

# 设置页面描述
st.markdown("""
    本应用允许您输入一个文章的URL，自动抓取内容并进行中文分词。
    我们将根据词频生成词云、条形图、饼图等多种可视化图表，并允许您根据词频过滤低频词汇。
    请在下方输入有效的URL并开始分析。
""")

# 用户输入文章URL
url = st.text_input("请输入文章的URL", "https://www.example.com")  # 修正了这里的引号

# 请求URL抓取文本内容
def fetch_text(url):
    if not url:  # 如果URL为空
        st.error("请输入有效的URL")
        return None
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'  # 手动设置编码
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except requests.exceptions.MissingSchema:
        st.error("无效的URL，请确保以 'http://' 或 'https://' 开头")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"请求失败: {e}")
        return None
# aa
# 确保在URL有效时获取文本
if url:
    text = fetch_text(url)
    if text:
        st.subheader("抓取到的文本内容（部分）:")
        st.text_area("文章内容", text[:500], height=200)  # 仅展示前500字符

        # 对文本分词，统计词频
        def tokenize_and_count(text):
            words = jieba.lcut(text)
            word_counts = Counter(words)
            return word_counts

        word_counts = tokenize_and_count(text)

        # 使用pyecharts绘制词云
        def create_wordcloud(word_counts):
            wordcloud = WordCloud()
            wordcloud.add("", word_counts.items(), word_size_range=[20, 100])
            wordcloud.set_global_opts(title_opts=opts.TitleOpts(title="词云"))
            return wordcloud

        wordcloud = create_wordcloud(word_counts)

        # 构建streamlit的st.sidebar进行图型筛选
        chart_types = ["词云", "条形图", "饼图", "散点图", "折线图", "雷达图", "K线图"]
        selected_chart = st.sidebar.selectbox("选择图表类型", chart_types)

        # 交互过滤低频词
        min_count = st.sidebar.slider("设置词频阈值", 1, 100, 10)
        filtered_word_counts = {word: count for word, count in word_counts.items() if count >= min_count}

        # 将 filtered_word_counts 转换为 Counter 对象，以便使用 most_common 方法
        filtered_word_counts = Counter(filtered_word_counts)

        # 展示词频排名前20的词汇
        top_20_words = filtered_word_counts.most_common(20)

        # 添加排序选项
        sort_order = st.sidebar.selectbox("选择排序方式", ["从高到低", "从低到高"])

        if sort_order == "从低到高":
            top_20_words = sorted(top_20_words, key=lambda x: x[1])  # 按照词频从低到高排序

        st.subheader(f"词频排名前20的词汇（{sort_order}）")
        st.write(top_20_words)

        # 根据选择的图表类型展示不同的图表
        st.subheader("词频可视化")
        if selected_chart == "词云":
            # 词云图直接嵌入网页
            html(wordcloud.render_embed(), height=800)  # 使用 render_embed() 生成 HTML
        elif selected_chart == "条形图":
            bar = Bar()
            bar.add_xaxis([word[0] for word in top_20_words])
            bar.add_yaxis("词频", [word[1] for word in top_20_words])
            bar.set_global_opts(title_opts=opts.TitleOpts(title="词频条形图"))
            html(bar.render_embed(), height=800)
        elif selected_chart == "饼图":
            pie = Pie()
            pie.add("", [list(z) for z in top_20_words])
            pie.set_global_opts(title_opts=opts.TitleOpts(title="词频饼图"))
            pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
            html(pie.render_embed(), height=800)
        elif selected_chart == "散点图":
            scatter = Scatter()
            scatter.add_xaxis([word[0] for word in top_20_words])
            scatter.add_yaxis("词频", [word[1] for word in top_20_words])
            scatter.set_global_opts(title_opts=opts.TitleOpts(title="词频散点图"))
            html(scatter.render_embed(), height=800)
        elif selected_chart == "折线图":
            line = Line()
            line.add_xaxis([word[0] for word in top_20_words])
            line.add_yaxis("词频", [word[1] for word in top_20_words])
            line.set_global_opts(title_opts=opts.TitleOpts(title="词频折线图"))
            html(line.render_embed(), height=800)
        elif selected_chart == "雷达图":
            radar = Radar()
            # 配置雷达图的指标项，确保指标数量与 top_20_words 中的词汇数量一致
            radar.add_schema(
                schema=[
                    opts.RadarIndicatorItem(name=word[0], max_=max(word[1] for word in top_20_words))
                    for word in top_20_words
                ]
            )
            # 在雷达图中添加数据，使用 zip 生成符合格式的数据
            radar.add("词频", [word[1] for word in top_20_words])
            radar.set_global_opts(title_opts=opts.TitleOpts(title="词频雷达图"))
            html(radar.render_embed(), height=800)
        elif selected_chart == "K线图":
            # 模拟K线图数据（开盘价，收盘价，最低价，最高价）
            kline_data = []
            for i, (word, freq) in enumerate(top_20_words):
                # 使用词频值作为开盘价、收盘价、最低价和最高价
                open_price = freq
                close_price = freq
                low_price = max(1, freq - 3)  # 取一个最小值避免为负数
                high_price = freq + 3  # 取一个偏高的值
                kline_data.append([open_price, close_price, low_price, high_price])

            # 创建K线图
            kline = Kline()
            kline.add_xaxis([word[0] for word in top_20_words])
            kline.add_yaxis("词频K线", kline_data)
            kline.set_global_opts(title_opts=opts.TitleOpts(title="词频K线图"))
            html(kline.render_embed(), height=800)

# 页面底部信息
st.markdown("""
    ---
    **提示**：您可以尝试使用其他文章URL，或调整词频阈值进行不同的分析！
    - 本应用使用 `jieba` 进行中文分词，`pyecharts` 用于图表生成。
    - 如果有任何问题，请通过下方评论区与我们联系。
""")