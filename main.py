import pandas as pd
import datetime as dt
import re
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import sys
import konlpy
from wordcloud import WordCloud, STOPWORDS

path_gothic = 'C:/Windows/Fonts/malgun.ttf'
font_property = fm.FontProperties(fname=path_gothic, size=12)

# 카카오톡 채팅 분석기
def get_chat_name(filename):
    """
    채팅방 이름 추출
    """
    chat_name_re = re.compile("(.+) 님과 카카오톡 대화")
    f = open(filename, "r", encoding="utf-8")
    line = f.readline()

    return re.findall(chat_name_re, line)


def preprocess_chat_text(filename):
    """
    카카오톡 대화 파일을 분석할수있게 데이터 가공
    """

    date_re = re.compile("-+ \d+년 \d+월 \d+일")
    invite_re = re.compile(".*님을 초대하였습니다.")
    exit_re = re.compile(".*님이 나갔습니다.")
    info_re = re.compile("\[([\w{2,3}]+)\] \[(오전|오후) ([\d:\s]+)\] (.*)")

    def is_date_line(_line):
        return bool(re.search(date_re, _line))

    def is_useless_line(_line):
        return bool(re.search(invite_re, _line)) or bool(re.search(exit_re, _line))

    def is_message_info_line(_line):
        return bool(re.search(info_re, _line))

    def is_message_line(_line):
        if (_line == False):
            return False
        ret = not (is_date_line(_line) or is_useless_line(_line) or is_message_info_line(_line))
        return ret

    def read_line(f):
        line = f.readline()
        if (line != ''):
            return line
        else:
            return False

    num_lines = sum(1 for line in open(filename, "r", encoding='utf-8'))
    cnt = 0
    loading_message = "대화 파일 읽는 중"
    print((loading_message))
    f = open(filename, "r", encoding="utf-8")

    line = f.readline()
    line = f.readline()
    line = f.readline()

    line = f.readline()
    current_time = dt.datetime.now()
    chat_data = []

    while (line):
        if (is_date_line(line)):
            date = re.findall("\d+", line)
            current_time = current_time.replace(int(date[0]), int(date[1]), int(date[2]))
            line = read_line(f)

        elif (is_useless_line(line)):
            line = read_line(f)

        elif (is_message_info_line(line)):
            message_block = []
            info = re.findall(info_re, line)
            speaker = info[0][0]
            meridiem = info[0][1]
            message = info[0][3]

            if (meridiem == "오전"):
                meridiem = info[0][2] + " AM"
            else:
                meridiem = info[0][2] + " PM"
            t = dt.datetime.strptime(meridiem, "%I:%M %p")
            current_time = current_time.combine(current_time.date(), t.time())
            line = read_line(f)

            while is_message_line(line):
                message += line
                line = read_line(f)

            message_block.extend([current_time, speaker, message])
            chat_data.append(message_block)
    f.close()
    chat_data_frame = pd.DataFrame(chat_data, columns=["Date", "Speaker", "Message"])
    
    return chat_data_frame


def build_pd_data(filename):
    """
    dataframe이 저장된 chat_data.csv 파일 생성
    """
    df = preprocess_chat_text(filename)
    df.Date = pd.to_datetime(df.Date)

    df["date"] = df['Date'].dt.strftime('%Y-%m-%d')
    df["year"] = df['Date'].dt.strftime('%Y')
    df["month"] = df['Date'].dt.strftime('%m')
    df["day"] = df['Date'].dt.strftime('%d')
    df["hour"] = df['Date'].dt.strftime('%H')
    df["min"] = df['Date'].dt.strftime('%m')

    len_list = []
    for i in range(len(df)):
        len_list.append(len(df["Message"][i]))
    df['length'] = len_list

    df.to_csv("chat_data.csv")


def tokenization(df):
    loading_message = "데이터 처리 중"
    print(loading_message)
    tk = konlpy.tag.Okt()
    topic_list = []
    l = len(df[MESSAGE])

    for i in range(l):
        expect_word = ["이모티콘", "사진", "어제", "오늘", "내일"]
        try:
            tmp = tk.nouns(df[MESSAGE][i])
        except:
            tmp = []
        finally:
            topic_list += tmp

    topic_list = (" ").join(topic_list)

    return topic_list


fig = plt.figure()
kakao_chat_filename = "KakaoTalk.txt"
csv_filename = "chat_data.csv"
DATE = "Date"
SPEAKER = "Speaker"
MESSAGE = "Message"
DATE_time_x = "date"
YEAR = "year"
MONTH = "month"
DAY = "day"
HOUR = "hour"
MINUTE = "min"
LENGTH = "length"


def display_page_1(df):
    fig = plt.figure()
    fig.suptitle('1페이지')
    plt.subplot(221)
    name = get_chat_name(kakao_chat_filename)
    plt.text(0.05, 0.90, "채팅방 이름 : " + name[0], fontsize=12, verticalalignment='top')
    start_date = df[DATE_time_x].min()[:10]
    end_date = df[DATE_time_x].max()[:10]
    plt.text(0.05, 0.70, "분석 기간 : " + start_date + " ~ " + end_date, fontsize=12, verticalalignment='top')
    plt.text(0.05, 0.50, "총 채팅 수 : " + str(df[MESSAGE].count()), fontsize=12, verticalalignment='top')
    plt.text(0.05, 0.30, "대화 인원 : " + str(len(df[SPEAKER].unique())), fontsize=12, verticalalignment='top')
    ax = plt.gca()
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)

    plt.subplot(222)
    df.groupby(HOUR)[MESSAGE].count().plot(title="시간대 별 대화량",grid=True,color="darkslategray").grid(alpha = 0.5)
    plt.subplot(223)
    df.groupby(DATE_time_x)[MESSAGE].count().sort_values(ascending=False)[:5].plot(kind="bar", title="가장 말이 많았던 날",color='c')
    plt.xticks(rotation=20)
    plt.subplot(224)
    df.groupby(SPEAKER)[MESSAGE].count().sort_values(ascending=True).plot(kind="barh",title="말 많은 사람 순위")

    plt.tight_layout(pad=2.0)
    pdf.savefig()


def display_page_2(df):
    fig = plt.figure()
    fig.suptitle('2페이지')

    plt.subplot(221)
    try:
        op1 = df[df[MESSAGE] == "이모티콘"].groupby(SPEAKER)[MESSAGE].count()
        op2 = df.groupby(SPEAKER)[MESSAGE].count()
        (op1.div(op2)*100).sort_values(
            ascending=True).plot(kind="barh",title="이모티콘 비율 순위")
    except:
        pass

    plt.subplot(222)
    try:
        df[(df[MESSAGE].str.contains("ㅠ|ㅜ"))].groupby(SPEAKER)[MESSAGE].count().sort_values(
            ascending=True).plot(kind="barh",title="눈물 많은 순위")
    except:
        pass

    plt.subplot(223)
    try:
        df[(df[MESSAGE].str.contains("ㅋ"))].groupby(SPEAKER)[MESSAGE].count().sort_values(
            ascending=True).plot(kind="barh",title="많이 웃은 순위")
    except:
        pass

    plt.subplot(224)
    try:
        swear_words = ["ㅅㅂ", "ㅂㅅ", "ㅄ","시발","병신","ㅅㄲ","새끼","쉬벌","시벌","개새","ㄱㅅㄲ"]
        df[(df[MESSAGE].str.contains(('|').join(swear_words)))].groupby(SPEAKER)[MESSAGE].count().sort_values(
         ascending=True).plot(kind="barh",title="욕 순위 ㅋㅋ")
    except:
        pass

    plt.tight_layout(pad=2.0)

    pdf.savefig()


def display_page_3(topic_list):
    fig = plt.figure()
    fig.suptitle('마지막 페이지\n\n자주 얘기한 주제')
    expect_word = ["이모티콘", "사진", "어제", "오늘", "내일"]
    stop_words = expect_word + list(STOPWORDS)

    wordcloud = WordCloud(stopwords=stop_words,width=800, height=400,font_path=path_gothic,
                          background_color='white',collocations=False).generate(topic_list)

    plt.imshow(wordcloud, interpolation='None')
    plt.axis('off')
    plt.tight_layout(pad=2.0)

    pdf.savefig()


if __name__ == '__main__':
    fname = font_property.get_name()
    plt.rc('font', family=fname)
    plt.rcParams["figure.figsize"] = (10, 6)

    df = build_pd_data(kakao_chat_filename)
    df = pd.read_csv(csv_filename)
    topic_list = tokenization(df)

    with PdfPages("output.pdf") as pdf:
        display_page_1(df)
        display_page_2(df)
        display_page_3(topic_list)
