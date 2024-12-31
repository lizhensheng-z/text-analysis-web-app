import streamlit as st
import requests
from bs4 import BeautifulSoup
import jieba
from collections import Counter
from pyecharts import options as opts
from pyecharts.charts import WordCloud, Bar, Pie, Scatter, Line, Radar, Kline
from streamlit.components.v1 import html
import plotly.express as px
import altair as alt
import pandas as pd
import pygal
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
#


# 创建气泡图
def create_bubble_chart(word_counts):
    # 准备数据
    top_words = word_counts.most_common(20)  # 获取前 20 个高频词
    words = [word[0] for word in top_words]
    freqs = [word[1] for word in top_words]
    lengths = [len(word) for word in words]  # 计算词的长度

    # 使用 Plotly Express 创建气泡图
    fig = px.scatter(
        x=words,  # X轴为词汇
        y=freqs,  # Y轴为词频
        size=freqs,  # 气泡大小由词频决定
        color=lengths,  # 气泡颜色由词的长度决定
        labels={"x": "词汇", "y": "词频", "color": "词长度"},
        title="词频气泡图",
    )
    return fig


# 创建交互式柱状图
def create_altair_bar_chart(word_counts):
    # 准备数据
    top_words = word_counts.most_common(20)  # 前 20 个高频词
    data = pd.DataFrame(top_words, columns=["词汇", "词频"])  # 转换为 DataFrame

    # 使用 Altair 创建柱状图
    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("词汇", sort="-y", title="词汇"),  # X轴为词汇
            y=alt.Y("词频", title="词频"),  # Y轴为词频
            tooltip=["词汇", "词频"]  # 悬停显示词汇和词频
        )
        .properties(title="交互式词频柱状图", width=600, height=400)  # 设置图表大小
    )
    return chart


# 创建动态折线图
# 创建 pygal 折线图
def create_pygal_line_chart(word_counts):
    top_words = word_counts.most_common(20)
    words = [word[0] for word in top_words]
    freqs = [word[1] for word in top_words]

    # 使用 Pygal 创建折线图
    line_chart = pygal.Line()
    line_chart.title = "词频动态折线图"
    line_chart.x_labels = words  # X轴为词汇
    line_chart.add("词频", freqs)  # 添加词频数据
    return line_chart


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
        chart_types = ["词云", "条形图", "饼图", "散点图", "折线图", "雷达图", "K线图", "箱线图", "热力图", "地理热力图", "气泡图", "交互式柱状图", "动态折线图"]
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
        # 在生成词云后添加讲解
        if selected_chart == "词云":
            html(wordcloud.render_embed(), height=800)  # 使用 render_embed() 生成 HTML
            st.markdown("""
                **词云图解释**：
                词云图展示了文章中最频繁出现的词汇。词汇的大小与其频率成正比，词频越高，词云中的词汇越大。词云图能够帮助我们直观地了解文章的主题和关键词。
            """)

        # 在生成条形图后添加讲解
        elif selected_chart == "条形图":
            bar = Bar()
            bar.add_xaxis([word[0] for word in top_20_words])
            bar.add_yaxis("词频", [word[1] for word in top_20_words])
            bar.set_global_opts(title_opts=opts.TitleOpts(title="词频条形图"))
            html(bar.render_embed(), height=800)
            st.markdown("""
                **条形图解释**：
                该条形图展示了文章中词汇的频率分布。每根条形代表一个词汇，条形的高度表示该词汇出现的次数。通过该图，用户可以清晰地看到哪些词汇在文章中占据主导地位。
            """)

        # 在生成饼图后添加讲解
        elif selected_chart == "饼图":
            pie = Pie()
            pie.add("", [list(z) for z in top_20_words])
            pie.set_global_opts(title_opts=opts.TitleOpts(title="词频饼图"))
            pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
            html(pie.render_embed(), height=800)
            st.markdown("""
                **饼图解释**：
                饼图展示了文章中不同词汇的相对频率。每个部分的大小代表该词汇的频率占总频率的比例。饼图帮助我们直观地比较不同词汇的出现比例。
            """)

        # 在生成散点图后添加讲解
        elif selected_chart == "散点图":
            scatter = Scatter()
            scatter.add_xaxis([word[0] for word in top_20_words])
            scatter.add_yaxis("词频", [word[1] for word in top_20_words])
            scatter.set_global_opts(title_opts=opts.TitleOpts(title="词频散点图"))
            html(scatter.render_embed(), height=800)
            st.markdown("""
                **散点图解释**：
                散点图通过每个点的位置表示词汇的词频。X轴为词汇，Y轴为词频，气泡的大小表示该词汇的出现频率。散点图可以帮助用户发现频率较高的词汇。
            """)

        # 在生成折线图后添加讲解
        elif selected_chart == "折线图":
            line = Line()
            line.add_xaxis([word[0] for word in top_20_words])
            line.add_yaxis("词频", [word[1] for word in top_20_words])
            line.set_global_opts(title_opts=opts.TitleOpts(title="词频折线图"))
            html(line.render_embed(), height=800)
            st.markdown("""
                **折线图解释**：
                该折线图展示了文章中高频词汇的词频变化趋势。X轴为词汇，Y轴为词频，线条的起伏反映了词汇出现频率的波动情况。适合用来观察不同词汇的频率变化。
            """)
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
            st.markdown("""
                **雷达图解释**：
                雷达图能够展示不同词汇的词频分布情况，每个轴代表一个词汇，轴的长度表示该词汇的出现频率。适合观察词汇的整体分布情况。
            """)
        elif selected_chart == "K线图":
            kline_data = []
            for i, (word, freq) in enumerate(top_20_words):
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
            st.markdown("""
                **K线图解释**：
                K线图通过显示每个词汇的开盘价、收盘价、最低价和最高价，来展示词汇频率的波动情况。每根K线代表一个词汇，K线的长度和颜色反映词频的波动情况。
            """)
        elif selected_chart == "气泡图":
            fig = create_bubble_chart(filtered_word_counts)
            st.plotly_chart(fig)
            st.markdown("""
                **气泡图解释**：
                气泡图通过显示每个词汇的频率和长度来展示词频的分布情况。气泡的大小表示词汇的频率，颜色表示词汇的长度，适合观察词汇的频率和长度的关系。
            """)
        elif selected_chart == "交互式柱状图":

            chart = create_altair_bar_chart(filtered_word_counts)
            st.altair_chart(chart, use_container_width=True)
            st.markdown("""
                **交互式柱状图解释**：
                该柱状图展示了文章中各词汇的频率分布，用户可以通过悬停查看每个词汇的详细信息。交互式柱状图允许用户更直观地比较不同词汇的词频。
            """)
        elif selected_chart == "动态折线图":
            # 获取图表的 HTML 并嵌入到 Streamlit 页面
            line_chart = create_pygal_line_chart(filtered_word_counts)
            html(line_chart.render(), height=400)
            st.markdown("""
                **动态折线图解释**：
                该折线图展示了文章中最频繁出现的词汇的变化趋势，能够帮助用户更好地理解不同词汇在文章中的出现频率变化。
            """)

# 页面底部信息
st.markdown("""
    ---
    **提示**：您可以尝试使用其他文章URL，或调整词频阈值进行不同的分析！
    - 本应用使用 `jieba` 进行中文分词，`pyecharts` 用于图表生成。
    - 如果有任何问题，请通过下方评论区与我们联系。
""")
