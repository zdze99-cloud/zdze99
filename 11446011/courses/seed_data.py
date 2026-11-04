"""選課系統示範資料(由原型 course-selection-standalone.html 轉出)。"""

ME = {'name': '萬睿鈞', 'sid': '11446011', 'dept': '資訊管理學系', 'year': 2}

DONE = {'CS101': '程式設計（一）', 'CS102': '程式設計（二）', 'CS201': '資料結構', 'CS202': '離散數學', 'MA101': '微積分'}

G_DEF = {'必修': [['作業', 30], ['期中考', 30], ['期末考', 40]],
 '選修': [['作業', 30], ['專題', 30], ['期末考', 40]],
 '通識': [['課堂參與', 20], ['小組報告', 40], ['期末報告', 40]],
 '體育': [['出席', 40], ['技能測驗', 60]]}

PH_DESC = {'1': '第一階段登記：填寫志願序，截止後依優先權重電腦分發。', '2': '第二階段加退選：即時處理、先搶先贏，名額額滿即無法加選。', '3': '特殊加選：輸入教師核發的授權碼，可超過人數上限加選。'}

PH_DATE = {'1': '08/10 09:00 – 08/16 17:00', '2': '09/08 12:30 – 09/19 17:00', '3': '09/20 09:00 – 09/24 17:00'}

COURSES = [{'id': 'CS301',
  'name': '演算法',
  'dept': '資訊工程學系',
  'year': 3,
  'type': '必修',
  'teacher': '陳建宏',
  'credits': 3,
  'slots': [[2, [3, 4]], [4, [3]]],
  'bld': '資訊館',
  'room': 'R201',
  'cap': 60,
  'enr': 58,
  'pre': 'CS201',
  'desc': '介紹演算法設計與分析的核心方法，包含分治法、動態規劃、貪婪法與圖論演算法，並探討 NP 完備性。',
  'topics': ['漸進分析與遞迴式', '分治法與排序', '動態規劃與貪婪法', '圖論與最短路徑', '網路流與 NP 完備性'],
  'book': 'Cormen et al., Introduction to Algorithms, 4th ed.'},
 {'id': 'CS302',
  'name': '作業系統',
  'dept': '資訊工程學系',
  'year': 3,
  'type': '必修',
  'teacher': '王明哲',
  'credits': 3,
  'slots': [[1, [6, 7, 8]]],
  'bld': '資訊館',
  'room': 'R105',
  'cap': 60,
  'enr': 60,
  'pre': 'CS201',
  'desc': '行程管理、排程、同步、記憶體管理、檔案系統與虛擬化，搭配 xv6 核心實作。',
  'topics': ['行程與執行緒', 'CPU 排程', '同步與死結', '記憶體與分頁', '檔案系統'],
  'book': 'Silberschatz, Operating System Concepts, 10th ed.'},
 {'id': 'CS315',
  'name': '機器學習導論',
  'dept': '資訊工程學系',
  'year': 3,
  'type': '選修',
  'teacher': '林俊杰',
  'credits': 3,
  'slots': [[3, [2, 3, 4]]],
  'bld': '資訊館',
  'room': 'R301',
  'cap': 45,
  'enr': 45,
  'code': True,
  'pre': 'CS201',
  'desc': '監督式與非監督式學習的理論與實作，涵蓋線性模型、決策樹、核方法與神經網路基礎。',
  'topics': ['學習理論與偏差變異', '線性與邏輯迴歸', '決策樹與集成方法', '支持向量機', '神經網路入門'],
  'book': 'Bishop, Pattern Recognition and Machine Learning'},
 {'id': 'CS320',
  'name': '計算機網路',
  'dept': '資訊工程學系',
  'year': 3,
  'type': '選修',
  'teacher': '張志豪',
  'credits': 3,
  'slots': [[2, [3, 4]], [4, [4]]],
  'bld': '資訊館',
  'room': 'R203',
  'cap': 55,
  'enr': 41,
  'desc': '自應用層至實體層的網路協定架構，包含 HTTP、TCP/IP、路由與無線網路。',
  'topics': ['應用層協定', '傳輸層與 TCP', '網路層與路由', '連結層', '網路安全'],
  'book': 'Kurose & Ross, Computer Networking, 8th ed.'},
 {'id': 'CS330',
  'name': '資料庫系統',
  'dept': '資訊工程學系',
  'year': 3,
  'type': '選修',
  'teacher': '林俊杰',
  'credits': 3,
  'slots': [[4, [6, 7, 8]]],
  'bld': '資訊館',
  'room': 'R202',
  'cap': 50,
  'enr': 32,
  'desc': '關聯式模型、SQL、正規化、交易處理與索引結構，並實作小型資料庫應用。',
  'topics': ['關聯模型與 SQL', 'ER 設計與正規化', '索引與查詢最佳化', '交易與並行控制', 'NoSQL 概論'],
  'book': 'Silberschatz, Database System Concepts, 7th ed.'},
 {'id': 'CS390',
  'name': '專題研究（一）',
  'dept': '資訊工程學系',
  'year': 4,
  'type': '必修',
  'teacher': '陳建宏',
  'credits': 2,
  'slots': [[5, [8, 9]]],
  'bld': '資訊館',
  'room': 'R401',
  'cap': 30,
  'enr': 10,
  'pre': 'CS301',
  'desc': '於指導教授實驗室進行研究專題，期末發表成果海報與口頭報告。',
  'topics': ['題目訂定', '文獻探討', '系統實作', '期中進度報告', '成果發表'],
  'book': '依指導教授指定'},
 {'id': 'MA201',
  'name': '線性代數',
  'dept': '應用數學系',
  'year': 2,
  'type': '必修',
  'teacher': '周育德',
  'credits': 3,
  'slots': [[1, [2, 3, 4]]],
  'bld': '理學院',
  'room': 'S110',
  'cap': 80,
  'enr': 71,
  'desc': '向量空間、線性轉換、矩陣分解、特徵值與內積空間。',
  'topics': ['線性方程組', '向量空間', '線性轉換', '特徵值與對角化', '內積與正交'],
  'book': 'Strang, Introduction to Linear Algebra, 6th ed.'},
 {'id': 'EN301',
  'name': '進階英文寫作',
  'dept': '外國語文學系',
  'year': 3,
  'type': '選修',
  'teacher': 'Emily Carter',
  'credits': 2,
  'slots': [[5, [3, 4]]],
  'bld': '外語大樓',
  'room': 'F305',
  'cap': 35,
  'enr': 20,
  'desc': '學術寫作結構、論證與引用格式，可抵免英文畢業門檻。',
  'topics': ['段落結構', '論說文', '研究摘要', '引用與 APA', '同儕審閱'],
  'book': '自編講義'},
 {'id': 'GE105',
  'name': '哲學與當代社會',
  'dept': '通識教育中心',
  'year': 0,
  'type': '通識',
  'area': '人文',
  'teacher': '吳宛真',
  'credits': 2,
  'slots': [[3, [6, 7]]],
  'bld': '文學院',
  'room': 'L203',
  'cap': 120,
  'enr': 88,
  'desc': '以哲學方法討論科技倫理、正義與公共議題。',
  'topics': ['什麼是哲學思考', '正義理論', '科技倫理', '自由與責任', '公共討論'],
  'book': 'Sandel, Justice'},
 {'id': 'GE210',
  'name': '環境科學與永續',
  'dept': '通識教育中心',
  'year': 0,
  'type': '通識',
  'area': '自然',
  'teacher': '鄭安琪',
  'credits': 2,
  'slots': [[5, [6, 7]]],
  'bld': '理學院',
  'room': 'S201',
  'cap': 100,
  'enr': 100,
  'desc': '氣候變遷、能源轉型與生態保育的科學基礎。',
  'topics': ['地球系統', '氣候變遷', '能源與碳排', '生物多樣性', '永續行動'],
  'book': '自編講義'},
 {'id': 'GE318',
  'name': '經濟學原理',
  'dept': '通識教育中心',
  'year': 0,
  'type': '通識',
  'area': '社會',
  'teacher': '劉冠廷',
  'credits': 2,
  'slots': [[4, [9, 10]]],
  'bld': '管理學院',
  'room': 'M101',
  'cap': 150,
  'enr': 120,
  'desc': '供需、市場結構、總體經濟指標與政策。',
  'topics': ['供給與需求', '彈性與福利', '市場結構', '國民所得', '貨幣與財政政策'],
  'book': 'Mankiw, Principles of Economics'},
 {'id': 'GE402',
  'name': '藝術賞析',
  'dept': '通識教育中心',
  'year': 0,
  'type': '通識',
  'area': '人文',
  'teacher': '蔡明蓉',
  'credits': 2,
  'slots': [[2, [6, 7]]],
  'bld': '藝術館',
  'room': 'A102',
  'cap': 90,
  'enr': 45,
  'desc': '從文藝復興到現代主義，學習觀看與詮釋藝術作品。',
  'topics': ['觀看的方法', '文藝復興', '印象派', '現代主義', '當代藝術'],
  'book': 'Gombrich, The Story of Art'},
 {'id': 'PE120',
  'name': '羽球（初級）',
  'dept': '體育室',
  'year': 0,
  'type': '體育',
  'teacher': '林志偉',
  'credits': 1,
  'slots': [[3, [8, 9]]],
  'bld': '體育館',
  'room': 'G2',
  'cap': 40,
  'enr': 37,
  'desc': '羽球基本握拍、步法與發球，期末進行單打比賽。',
  'topics': ['握拍與步法', '高遠球', '切球與殺球', '雙打輪轉', '期末賽'],
  'book': '無'},
 {'id': 'PE135',
  'name': '游泳（中級）',
  'dept': '體育室',
  'year': 0,
  'type': '體育',
  'teacher': '許雅雯',
  'credits': 1,
  'slots': [[6, [3, 4]]],
  'bld': '游泳館',
  'room': 'P1',
  'cap': 30,
  'enr': 12,
  'desc': '自由式與蛙式技術修正，提升耐力。',
  'topics': ['水中呼吸', '自由式', '蛙式', '轉身技巧', '400 公尺測驗'],
  'book': '無'}]

REQUESTS = [{'rid': 1,
  'course': 'CS315',
  'name': '萬睿鈞',
  'sid': '11446011',
  'dept': '資管二甲',
  'reason': '專題方向為機器學習，已修畢資料結構。',
  'status': 'pending'},
 {'rid': 2,
  'course': 'CS315',
  'name': '陳柏宇',
  'sid': 'B11202045',
  'dept': '資工三',
  'reason': '第一階段未中籤，下學期將出國交換。',
  'status': 'pending'},
 {'rid': 3,
  'course': 'CS315',
  'name': '黃子晴',
  'sid': 'B11005012',
  'dept': '電機三',
  'reason': '輔系資工，需本課程學分。',
  'status': 'pending'},
 {'rid': 4,
  'course': 'CS315',
  'name': '張家豪',
  'sid': 'B10902088',
  'dept': '資工四',
  'reason': '應屆畢業，最後一次修課機會。',
  'status': 'approved',
  'code': 'K7QX-29FD'},
 {'rid': 5,
  'course': 'CS315',
  'name': '吳思妤',
  'sid': 'B11303021',
  'dept': '應數三',
  'reason': '已修線性代數與機率統計。',
  'status': 'pending'},
 {'rid': 6,
  'course': 'CS315',
  'name': '許承恩',
  'sid': 'B11202077',
  'dept': '資工三',
  'reason': '想多修一門課。',
  'status': 'rejected'},
 {'rid': 7,
  'course': 'CS330',
  'name': '蔡宜庭',
  'sid': 'B11202010',
  'dept': '資工三',
  'reason': '與實習時間調整後可修。',
  'status': 'pending'}]

HISTORY = [{'t': '08/12 10:02', 'stage': '第一階段', 'act': '登記志願', 'course': 'CS301 演算法', 'ok': True, 'res': '已登記'},
 {'t': '08/12 10:03', 'stage': '第一階段', 'act': '登記志願', 'course': 'CS315 機器學習導論', 'ok': True, 'res': '已登記'},
 {'t': '08/12 10:05', 'stage': '第一階段', 'act': '登記志願', 'course': 'MA201 線性代數', 'ok': True, 'res': '已登記'},
 {'t': '08/18 09:00', 'stage': '第一階段', 'act': '分發', 'course': 'CS301 演算法', 'ok': True, 'res': '中籤'},
 {'t': '08/18 09:00', 'stage': '第一階段', 'act': '分發', 'course': 'CS315 機器學習導論', 'ok': False, 'res': '未中籤'},
 {'t': '08/18 09:00', 'stage': '第一階段', 'act': '分發', 'course': 'MA201 線性代數', 'ok': True, 'res': '中籤'},
 {'t': '08/18 09:00', 'stage': '第一階段', 'act': '分發', 'course': 'GE105 哲學與當代社會', 'ok': True, 'res': '中籤'},
 {'t': '08/18 09:00', 'stage': '第一階段', 'act': '分發', 'course': 'PE120 羽球（初級）', 'ok': True, 'res': '中籤'},
 {'t': '09/08 12:31', 'stage': '第二階段', 'act': '加選', 'course': 'CS330 資料庫系統', 'ok': True, 'res': '成功'},
 {'t': '09/08 12:40', 'stage': '第二階段', 'act': '退選', 'course': 'GE210 環境科學與永續', 'ok': True, 'res': '成功'}]


# ---- 擴充課程(讓查詢頁有更多課可以篩選) ----
def _c(id, name, dept, year, type, teacher, credits, slots, bld, room, cap, enr, desc, topics, book="無", **extra):
    return dict(id=id, name=name, dept=dept, year=year, type=type, teacher=teacher, credits=credits,
                slots=slots, bld=bld, room=room, cap=cap, enr=enr, desc=desc, topics=topics, book=book, **extra)


CS, EE, MA, EN, GE, PE = "資訊工程學系", "電機工程學系", "應用數學系", "外國語文學系", "通識教育中心", "體育室"

EXTRA_COURSES = [
    _c("CS210", "數位邏輯設計", CS, 2, "必修", "黃俊傑", 3, [[2, [1, 2]], [4, [1]]], "資訊館", "R101", 60, 55,
       "布林代數、組合與序向邏輯電路設計，搭配 FPGA 實驗。", ["布林代數", "組合邏輯", "正反器", "有限狀態機", "FPGA 實作"],
       "Mano, Digital Design, 6th ed."),
    _c("CS303", "計算機組織", CS, 3, "必修", "張志豪", 3, [[5, [2, 3, 4]]], "資訊館", "R102", 60, 41,
       "指令集架構、管線化、快取與記憶體階層。", ["指令集架構", "算術邏輯單元", "管線化", "快取", "虛擬記憶體"],
       "Patterson & Hennessy, Computer Organization and Design", pre="CS102"),
    _c("CS325", "編譯器設計", CS, 3, "選修", "陳建宏", 3, [[5, [6, 7, 8]]], "資訊館", "R203", 40, 22,
       "詞法分析、語法分析、語意檢查與程式碼產生，期末完成小型編譯器。", ["詞法分析", "LL / LR 剖析", "語意分析", "中間碼", "最佳化"],
       "Aho et al., Compilers: Principles, Techniques, and Tools", pre="CS201"),
    _c("CS335", "資訊安全導論", CS, 3, "選修", "黃俊傑", 3, [[4, [2, 3, 4]]], "資訊館", "R301", 50, 49,
       "密碼學基礎、網路攻防與安全程式設計。", ["古典與現代密碼", "公鑰系統", "網頁安全", "緩衝區溢位", "CTF 實作"],
       "Stallings, Cryptography and Network Security"),
    _c("CS340", "軟體工程", CS, 3, "選修", "王明哲", 3, [[1, [2, 3, 4]]], "資訊館", "R204", 50, 30,
       "需求分析、設計模式、測試與敏捷開發，以小組專案實作。", ["需求分析", "UML", "設計模式", "測試與 CI", "敏捷開發"],
       "Sommerville, Software Engineering, 10th ed."),
    _c("CS350", "電腦圖學", CS, 3, "選修", "張志豪", 3, [[2, [8, 9, 10]]], "資訊館", "R202", 40, 18,
       "座標轉換、光柵化、著色與 GPU 程式設計。", ["座標轉換", "光柵化", "光照模型", "材質貼圖", "Shader 程式"],
       "Marschner & Shirley, Fundamentals of Computer Graphics"),
    _c("CS360", "雲端運算", CS, 4, "選修", "李佳穎", 3, [[3, [6, 7, 8]]], "資訊館", "R302", 40, 40,
       "虛擬化、容器、分散式儲存與雲端服務架構。", ["虛擬化", "Docker 與 Kubernetes", "分散式儲存", "無伺服器架構", "雲端成本"],
       "Erl, Cloud Computing: Concepts, Technology & Architecture", code=True),
    _c("CS410", "深度學習", CS, 4, "選修", "李佳穎", 3, [[1, [6, 7, 8]]], "資訊館", "R301", 40, 37,
       "類神經網路、CNN、RNN 與 Transformer,搭配 PyTorch 實作。", ["多層感知器", "反向傳播", "CNN", "Transformer", "期末專題"],
       "Goodfellow et al., Deep Learning", pre="CS315"),
    _c("EE201", "電路學", EE, 2, "必修", "楊淑芬", 3, [[1, [2, 3, 4]]], "電機館", "E201", 70, 63,
       "直流與交流電路分析、網路定理與暫態響應。", ["克希荷夫定律", "網路定理", "RC / RL 暫態", "相量分析", "功率"],
       "Hayt, Engineering Circuit Analysis"),
    _c("EE301", "訊號與系統", EE, 3, "必修", "楊淑芬", 3, [[3, [2, 3, 4]]], "電機館", "E203", 60, 44,
       "連續與離散訊號、傅立葉轉換、拉普拉斯與 Z 轉換。", ["訊號分類", "LTI 系統", "傅立葉轉換", "拉普拉斯轉換", "Z 轉換"],
       "Oppenheim, Signals and Systems"),
    _c("EE310", "嵌入式系統", EE, 3, "選修", "黃俊傑", 3, [[4, [6, 7, 8]]], "電機館", "E305", 35, 35,
       "微控制器架構、周邊介面與即時作業系統。", ["ARM 架構", "GPIO 與中斷", "UART / SPI / I2C", "RTOS", "期末作品"]),
    _c("MA202", "機率與統計", MA, 2, "必修", "周育德", 3, [[2, [2, 3, 4]]], "理學院", "S112", 80, 71,
       "機率模型、隨機變數、估計與假設檢定。", ["機率公理", "隨機變數", "常見分佈", "估計", "假設檢定"],
       "Ross, A First Course in Probability", pre="MA101"),
    _c("MA310", "數值方法", MA, 3, "選修", "周育德", 3, [[4, [9, 10]], [2, [5]]], "理學院", "S110", 50, 26,
       "方程求根、內插、數值積分與微分方程數值解。", ["誤差分析", "求根法", "內插與擬合", "數值積分", "常微分方程"],
       "Burden & Faires, Numerical Analysis"),
    _c("EN201", "英語口語表達", EN, 2, "選修", "Emily Carter", 2, [[1, [8, 9]]], "外語大樓", "F201", 30, 28,
       "簡報、討論與即席演說練習。", ["自我介紹", "小組討論", "簡報技巧", "即席演說", "期末簡報"]),
    _c("EN220", "學術英文閱讀", EN, 2, "選修", "Emily Carter", 2, [[3, [3, 4]]], "外語大樓", "F203", 35, 20,
       "閱讀學術論文的策略與摘要寫作。", ["略讀與掃讀", "論文結構", "字彙策略", "摘要寫作", "批判閱讀"]),
    _c("GE120", "哲學概論", GE, 0, "通識", "吳宛真", 2, [[1, [6, 7]]], "文學院", "L105", 80, 60,
       "從知識論、倫理學到形上學，認識哲學的基本問題。", ["何謂哲學", "知識論", "倫理學", "心靈哲學", "自由意志"], area="人文"),
    _c("GE215", "能源與永續發展", GE, 0, "通識", "鄭安琪", 2, [[4, [6, 7]]], "理學院", "S205", 80, 33,
       "認識能源結構、再生能源與淨零轉型。", ["能源概論", "化石燃料", "再生能源", "碳排與淨零", "政策案例"], area="自然"),
    _c("GE230", "天文學入門", GE, 0, "通識", "鄭安琪", 2, [[2, [8, 9]]], "理學院", "S301", 100, 97,
       "從太陽系到宇宙學，搭配夜間觀星活動。", ["天球座標", "太陽系", "恆星演化", "星系", "宇宙學"], area="自然"),
    _c("GE305", "法律與生活", GE, 0, "通識", "劉冠廷", 2, [[5, [8, 9]]], "管理學院", "M203", 90, 45,
       "以生活案例認識民法、刑法與消費者保護。", ["法律體系", "契約與租賃", "消費者保護", "網路法律", "勞動權益"], area="社會"),
    _c("GE330", "心理學概論", GE, 0, "通識", "吳宛真", 2, [[3, [6, 7]]], "文學院", "L301", 120, 120,
       "認識知覺、學習、記憶、動機與社會心理。", ["心理學方法", "知覺", "學習與記憶", "動機與情緒", "社會心理"], area="社會"),
    _c("PE140", "籃球（初級）", PE, 0, "體育", "何家豪", 1, [[2, [6, 7]]], "體育館", "G1", 40, 25,
       "運球、傳球、投籃與基本戰術。", ["運球", "傳接球", "投籃", "防守", "分組比賽"]),
    _c("PE150", "瑜珈", PE, 0, "體育", "許雅雯", 1, [[5, [3, 4]]], "體育館", "G3", 30, 29,
       "基礎體位法與呼吸練習，提升柔軟度與核心肌力。", ["呼吸法", "站姿", "坐姿與扭轉", "核心訓練", "放鬆冥想"]),
]
COURSES += EXTRA_COURSES


# ---- 大量課程:每個系所在週一到週日、第 1–10 節都有課,讓任何單一篩選都找得到 ----
import random as _random

_BLOCKS = [[1, 2, 3], [4, 5], [6, 7, 8], [9, 10]]
_GENERIC_TOPICS = ["課程導論", "核心概念", "案例討論", "實作練習", "期末報告"]

# (前綴, 系所, 大樓, 教室代號, 教師, 課名 14 門 × 甲乙兩班)
_DEPTS = [
    ("CS", CS, "資訊館", "R", ["黃俊傑", "陳建宏", "張志豪", "邱文彥"],
     ["計算機概論", "物件導向程式設計", "組合語言", "系統程式", "網路程式設計", "人工智慧", "自然語言處理",
      "電腦視覺", "平行程式設計", "行動應用程式開發", "網頁程式設計", "分散式系統", "資料探勘", "計算理論"]),
    ("EE", EE, "電機館", "E", ["楊淑芬", "謝承翰", "羅志明"],
     ["電子學（一）", "電子學（二）", "電磁學", "控制系統", "通訊原理", "數位訊號處理", "電力系統",
      "半導體元件", "微處理機", "類比積體電路", "天線工程", "電機機械", "影像處理", "無線網路"]),
    ("MA", MA, "理學院", "S", ["周育德", "江明珠", "潘建國"],
     ["微積分（二）", "高等微積分", "常微分方程", "偏微分方程", "抽象代數", "實變函數論", "複變函數論",
      "數理統計", "迴歸分析", "作業研究", "數論", "圖論", "拓樸學", "金融數學"]),
    ("EN", EN, "外語大樓", "F", ["Emily Carter", "David Miller", "葉佩君"],
     ["英文作文", "英語聽講練習", "英國文學史", "美國文學", "語言學概論", "英語語音學", "翻譯理論與實務",
      "莎士比亞", "兒童文學", "英語教學法", "跨文化溝通", "商用英文", "英美小說選讀", "口譯入門"]),
    ("IM", "資訊管理學系", "管理學院", "M", ["郭家瑋", "曾雅琪", "洪志明"],
     ["管理學", "會計學", "經濟學", "資訊管理導論", "系統分析與設計", "資料庫管理", "管理數學",
      "統計學", "作業管理", "電子商務", "企業資源規劃", "商業智慧", "資訊安全管理", "專案管理"]),
]
_GE = [("中國文學經典", "人文"), ("台灣史", "人文"), ("音樂欣賞", "人文"), ("電影與文化", "人文"), ("東亞文化", "人文"),
       ("生命科學概論", "自然"), ("化學與生活", "自然"), ("物理之美", "自然"), ("氣候變遷", "自然"),
       ("社會學概論", "社會"), ("政治學入門", "社會"), ("媒體識讀", "社會"), ("性別與社會", "社會"), ("創意思考", "社會")]
_GE_PLACES = [("文學院", "L"), ("理學院", "S"), ("管理學院", "M"), ("藝術館", "A")]
_GE_TEACHERS = ["吳宛真", "鄭安琪", "劉冠廷", "蔡明蓉", "簡美玲"]
_PE = ["桌球（初級）", "網球（初級）", "排球（初級）", "足球（初級）", "壘球", "有氧舞蹈", "重量訓練",
       "太極拳", "跆拳道", "游泳（初級）", "慢跑與體適能", "飛盤", "攀岩", "匹克球"]
_PE_PLACES = [("體育館", "G"), ("游泳館", "P")]
_PE_TEACHERS = ["林志偉", "許雅雯", "何家豪"]

# 新增教師的登入帳號(seed_demo 會一併建立)
EXTRA_TEACHER_ACCOUNTS = {
    "邱文彥": "chiu", "謝承翰": "hsieh", "羅志明": "lo", "江明珠": "chiang", "潘建國": "pan",
    "David Miller": "miller", "葉佩君": "yeh", "郭家瑋": "kuo", "曾雅琪": "tseng", "洪志明": "hung", "簡美玲": "chien",
}


def _generate():
    rng = _random.Random(11446011)
    taken = {c["id"] for c in COURSES} | set(DONE)
    out = []

    def seats():
        cap = rng.choice([30, 40, 50, 60, 80])
        enr = cap if rng.random() < 0.15 else rng.randint(cap // 4, cap - 1)
        return cap, enr

    def new_code(prefix, year, seq):
        n = 70
        while f"{prefix}{year}{n}" in taken:
            n += 1
        code = f"{prefix}{year}{n}"
        taken.add(code)
        return code

    slots = [(d, b) for d in range(1, 8) for b in range(len(_BLOCKS))]  # 7 天 × 4 時段 = 28
    for k, (prefix, dept, bld, rp, teachers, names) in enumerate(_DEPTS):
        for i, (d, b) in enumerate(slots):
            x = k + d + b
            year = x % 4 + 1
            ctype = "必修" if (x // 4 + k + d) % 2 == 0 else "選修"
            ps = _BLOCKS[b]
            cap, enr = seats()
            name = f"{names[i % 14]} {'甲班' if i < 14 else '乙班'}"
            out.append(_c(new_code(prefix, year, i), name, dept, year, ctype, teachers[(d + b) % len(teachers)],
                          len(ps), [[d, ps]], bld, f"{rp}{100 * (b + 1) + d:03d}", cap, enr,
                          f"{name.split()[0]}：由{dept}開設，涵蓋核心理論與實作練習。", _GENERIC_TOPICS,
                          "授課教師指定", **({"code": True} if enr == cap and rng.random() < 0.3 else {})))
    for i, (d, b) in enumerate(slots):
        ps = _BLOCKS[b]
        gname, area = _GE[i % 14]
        bld, rp = _GE_PLACES[i % 4]
        cap, enr = seats()
        out.append(_c(new_code("GE", 5, i), f"{gname} {'甲班' if i < 14 else '乙班'}", GE, 0, "通識",
                      _GE_TEACHERS[(d + b) % 5], len(ps), [[d, ps]], bld, f"{rp}{200 + 10 * b + d}", cap * 2, enr * 2,
                      f"{gname}：通識{area}領域課程，培養跨領域視野。", _GENERIC_TOPICS, area=area))
        pname = _PE[i % 14]
        bld, rp = _PE_PLACES[1 if "游泳" in pname else 0]
        cap, enr = seats()
        out.append(_c(new_code("PE", 2, i), f"{pname} {'甲班' if i < 14 else '乙班'}", PE, 0, "體育",
                      _PE_TEACHERS[(d + b) % 3], 1, [[d, _BLOCKS[b]]], bld, f"{rp}{b + 1}{d}",
                      min(cap, 40), min(enr, 40), f"{pname}：基本動作、體能訓練與分組練習。", _GENERIC_TOPICS))
    return out


GENERATED_COURSES = _generate()
COURSES += GENERATED_COURSES
