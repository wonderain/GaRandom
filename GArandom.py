import json
import sys
import os,locale
import traceback
from random import sample
from window import *
#from pool_window import *
import time
from pypinyin import lazy_pinyin
from fixed_pool import *
from  weapon_info import *


# 返回格式化时间
def sft():
    locale.setlocale(locale.LC_ALL,'en')
    return time.strftime('%H:%M:%S', time.localtime())

# 装饰器，用于计时
def timer(func):
    def func_in():
        start_time = time.time()
        func()
        end_time = time.time()
        spend_time = (end_time - start_time)/60
        print("Spend_time:{} min".format(spend_time))
    return func_in

# 按行读txt，返回列表
def read_txt_line(path):
    lines=[]
    with open(path,'r',encoding='utf-8') as f:
        for line in f.readlines():
            line=line.replace('\n','')
            if '#' in line:
                line=line[:line.find('#')]
            if line=='':
                continue
            lines.append(line)
    return lines

# 保存json
def write_json(path,data):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data,ensure_ascii=False,indent=4))

# 用于加密数字，给定数字，返回同样数位的双射对应值。
def encrypt_num():
    pass

# 加载json格式
def load_json(path):
    try:
        if not os.path.exists(path):
            return False
        with open(path, 'r', encoding='utf-8') as f:
            result = json.load(f)
        return result
    except Exception as e:
        print(e.args)
        return False

# 用于V2的名字列表大更新1，从名字列表变为字典，每个玩家增加多个键:'color','random_times','last_time'，如果name_list_json是字符列表，但是不改变原文件名
def name_list_json_updata1():
    name_list = load_json('name_list.json')
    try:
        if len(name_list) and type(name_list[0])==type(''):
            new_name_dict= {}
            for i in name_list:
                new_name_dict[i]={'color':0,'random_times':0,'last_time':0}
            write_json('name_list.json', new_name_dict)
    except:
        pass


# 获取装备的prc资源图标，输入装备名字，返回icon以及是否曾用名
def get_weapon_prc_icon(weapon_name):
    # 绘制装备图标
    now_name=False
    icon=False
    if weapon_name in weapon_info_dict:  # 如果名字在列表中
        icon = QtGui.QPixmap(':weapon_icon/weapons_icon/%s.png' % weapon_name)
    elif weapon_name in weapon_used2now_dict:  # 如果出现在曾用名栏目，则重定向回现在的名字
        now_name=weapon_used2now_dict[weapon_name]
        icon = QtGui.QPixmap(':weapon_icon/weapons_icon/%s.png' % now_name)
    return icon,now_name


# 展现装备池信息用
class pool_show_window(QtWidgets.QMainWindow):
    def __init__(self):
        super(pool_show_window,self).__init__()
        self.resize(250,250)
        self.setWindowFlags(QtCore.Qt.Window|QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.WindowMaximizeButtonHint|QtCore.Qt.MSWindowsFixedSizeDialogHint|QtCore.Qt.WindowCloseButtonHint)
        self.list=QtWidgets.QListWidget(self)
        self.ban_list=QtWidgets.QListWidget(self)
        self.list.resize(250,250)
        self.list.show()


    def Open(self,title,weapon_list):
        self.setWindowTitle(title)
        self.list.clear()
        try:
            for weapon in weapon_list:
                icon,now_name=get_weapon_prc_icon(weapon)
                if icon:
                    show_more_name=' (' + now_name + ')'  if now_name else ''
                    item = QtWidgets.QListWidgetItem(QtGui.QIcon(icon),weapon+show_more_name)
                else:
                    item = QtWidgets.QListWidgetItem(weapon)
                if weapon in weapon_info_dict:
                    detail=['%s : %s'%(k,v) for k,v in weapon_info_dict[weapon].items()]
                    text='\n'.join(detail)
                    item.setToolTip(text)
                elif now_name:
                    detail = ['%s : %s' % (k, v) for k, v in weapon_info_dict[now_name].items()]
                    text = '\n'.join(detail)
                    item.setToolTip(text)
                self.list.addItem(item)
        except:
            print(traceback.format_exc())
        self.show()

# 主窗口函数，输入UI，增加命令
class MainWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self,parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.desktop=QtWidgets.QApplication.desktop()
        self.setupUi(self)
        self.resize(self.width(), self.height() - 260)
        self.name_colors = [(0,0,0,255),(255,0,0,255), (0,0,255,255),(0,100,0,255), (255,150,0,255), (105,105,105,150)]


        '''确定用户地址和记录存放地址'''
        self.user_path=os.environ['USERPROFILE'].replace('\\','/')+'/Documents/'
        if not os.path.exists(self.user_path):
            self.user_path = os.environ['USERPROFILE'].replace('\\', '/')
            if not os.path.exists(self.user_path):
                self.user_path =''
        self.record_path=self.user_path+'rand_times_record.json'
        self.reset_rand_record()

        '''读取选手名单和顺序'''
        name_list_json_updata1()
        self.name_dict = load_json('name_list.json')
        init_set={'mh':0,'pn':'杰克池v1.0','tt':0,'nt':0,'color':0,'random_times':0,'last_time':0}
        if not self.name_dict:
            # 如果没有名单，那么就创建一个名单，且名单中构建一个存放设定的条目(v3.06起)
            # mh用于存放加密的刷新时间,pn表示上一次选择的装备池,tt/nt是干扰项
            self.name_dict = {'init':init_set}
            self.error_label.setText('未找到选手名单本地文件')
        if 'init' not in self.name_dict:# 又多了一个版本更新(v3.06)而增加的东西哇咔咔
            self.name_dict['init']=init_set
        self.join_list = []  # 参赛名单
        self.comboBox.currentIndexChanged.connect(self.change_order)
        self.name_listwidget_order = True
        self.change_order() #change_order其实才是真正的显示选手名单的函数，需要在里面排除'init'这一项


        '''随机装备区初始化'''
        self.pool_show=pool_show_window()
        self.comboBox_2.currentTextChanged.connect(self.when_pool_change)
        self.renew_pools() #初始化装备池选择

        '''手动记录设置'''
        self.manual_area=False
        self.manual_color=[(178,34,34,255),(255,69,0,255),(255,165,0,255),(154,205,50,255),(0,255,0,255),(32,178,170,255),
                           (0,255,255,255),(70,130,180,255),(0,0,255,255),(160,32,240,255),(186,85,211,255),(219,112,147,255)]
        self.manual_labels=[self.manual_label_1,self.manual_label_2,self.manual_label_3,self.manual_label_4,
                            self.manual_label_5,self.manual_label_6,self.manual_label_7,self.manual_label_8,
                            self.manual_label_9,self.manual_label_10,self.manual_label_11,self.manual_label_12,self.manual_label_13]
        for l in self.manual_labels:
            l.setText('')
        self.manual_list = []
        self.manual_record=[]   # 当前手动记录
        self.manual_total_record=[] # 全部手动记录（包含撤销的信息，只当录入新记录时和当前记录同步）
        self.manual_addnsub=[0 for i in range(12)]  # 手动补充记录，在记录中额外出现

    # 在玩家档中显示某个玩家
    def show_player(self,name,info):
        if name == 'init':
            return False
        item=QtWidgets.QListWidgetItem()
        item.setText(name)
        t=time.strftime('%y-%m-%d', time.localtime(info['last_time'])) if info['last_time'] else '0'
        item.setToolTip('总参与次数: %d 次\n最近参与时间: %s' % (info['random_times'], t))
        self.name_listwidget.addItem(item)
        # 添加颜色
        self.set_color(self.name_listwidget.count() - 1, info['color'])


    # 改变排列方式
    def change_order(self):
        self.name_listwidget.clear()
        if self.comboBox.currentIndex()==3:
            for name,info in sorted(self.name_dict.items(),key=lambda x:lazy_pinyin(x[0]),reverse=self.name_listwidget_order):
                self.show_player(name,info)
        else:
            title='color' if self.comboBox.currentIndex()==1 else 'random_times' if self.comboBox.currentIndex()==0 else 'last_time'
            for name,info in sorted(self.name_dict.items(),key=lambda x:x[1][title],reverse=self.name_listwidget_order):
                self.show_player(name,info)

    # 更改升降顺序
    def turn_order(self):
        self.name_listwidget_order = not self.name_listwidget_order
        self.change_order()


    # 通过隐藏文件的形式记录。放入一个新的时间计数（随机次数），并将超过一分钟以上的计数删除，更新计数信息，并最后返回一分钟以内的计数次数
    def new_rand_record(self):
        if not os.path.exists(self.record_path):
            write_json(self.record_path,[])
            #win32api.SetFileAttributes(self.record_path,win32con.FILE_ATTRIBUTE_HIDDEN)
            rand_times=[]
        else:
            rand_times=load_json(self.record_path)
        new_list=[]
        now_time=time.time()
        for i in rand_times:
            if now_time-i<=60*5:
                new_list.append(i)
        new_list.append(now_time)
        write_json(self.record_path,new_list)
        self.label_6.setText('五分钟内共随机%d次 当前：%s'%(len(new_list),sft()))
        return len(new_list)

    # 重置随即次数记录
    def reset_rand_record(self):
        self.label_6.setText('')


    #将当前选择名字放到参赛框内
    def choose(self):
        if self.name_listwidget.currentItem() is None:
            return False
        items=self.name_listwidget.selectedItems()
        for item in items:
            name = item.text()
            if name not in self.join_list:
                self.join_listwidget.addItem(name)
                self.join_list.append(name)
                self.label_2.setText('参赛列表(%d人)'%len(self.join_list))
                self.reset_rand_record()
        #self.name_listwidget.clearSelection() # 清除选择

    # 设置名字listitem颜色
    def set_color(self,index,color_index):
        color=QtGui.QColor(self.name_colors[color_index][0],self.name_colors[color_index][1],self.name_colors[color_index][2],self.name_colors[color_index][3])
        self.name_listwidget.item(index).setForeground(color)

    # 改变名字颜色
    def change_name_color(self):
        if not len(self.name_dict) or self.name_listwidget.currentItem() is None:
            return False
        i_s = self.name_listwidget.selectedIndexes()
        for i in i_s:
            index=i.row()
            name = self.name_listwidget.item(index).text()
            now_color_index=self.name_dict[name]["color"]
            to_color_index=(now_color_index+1)%len(self.name_colors)
            self.set_color(index,to_color_index)
            self.name_dict[name]["color"] =to_color_index
            write_json('name_list.json', self.name_dict)

    #将当前选择名字从参赛框中删除
    def unchoose(self):
        if self.join_listwidget.currentItem() is None:
            return False
        if self.join_listwidget.count()==0:
            return False
        select_items = self.join_listwidget.selectedItems()
        select_name=[]
        for item in select_items:
            self.join_list.remove(item.text())
            self.label_2.setText('参赛列表(%d人)'%len(self.join_list))
            select_name.append(item.text())
            self.reset_rand_record()
        for s_name in select_name:
            for i in range(self.join_listwidget.count()):
                item=self.join_listwidget.item(i)
                if item.text()== s_name:
                    self.join_listwidget.removeItemWidget(self.join_listwidget.takeItem(i))
                    break

    # 添加玩家数据
    def add_name(self):
        name=self.lineEdit.text()
        if name!='' and name not in self.name_dict:
            item = QtWidgets.QListWidgetItem()
            item.setText(name)
            item.setToolTip('总参与次数: 0 次\n最近参与时间: 0')
            self.name_listwidget.addItem(name)
            self.name_dict[name]={"color": 0,"random_times": 0,"last_time": 0}
            write_json('name_list.json', self.name_dict)
    # 删除玩家数据
    def del_name(self):
        if self.name_listwidget.currentItem() is None:
            return False
        if self.name_listwidget.count()==0:
            return False
        del self.name_dict[self.name_listwidget.currentItem().text()]
        write_json('name_list.json', self.name_dict)
        select_row = self.name_listwidget.currentRow()
        item = self.name_listwidget.takeItem(select_row)
        del item


    # 随机分队
    def rand_team(self):
        if not len(self.join_list):
            return False
        #print(len(self.join_list)/2)
        if len(self.join_list)%2!=0:
            self.error_label.setText('参赛人数不为偶数')
        else:
            self.listWidget_A.clear()
            self.listWidget_B.clear()

            team_A_manual,team_B_manual =[],[]
            for index in range(self.join_listwidget.count()):
                if self.join_listwidget.item(index).foreground().color().getRgb()==(255,0,0,255):
                    team_A_manual.append(self.join_listwidget.item(index).text())
                elif self.join_listwidget.item(index).foreground().color().getRgb()==(0, 0, 255, 255):
                    team_B_manual.append(self.join_listwidget.item(index).text())
            if len(team_A_manual)>int(len(self.join_list)/2) or len(team_B_manual)>int(len(self.join_list)/2):
                self.error_label.setText('手动添加的队伍人数超过队伍的一半，无法分队')
                return False
            remain_list=[i for i in self.join_list if i not in team_A_manual+team_B_manual]
            team_A=sample(remain_list,int(len(self.join_list)/2)-len(team_A_manual))+team_A_manual
            team_B=[i for i in remain_list if i not in team_A]+team_B_manual
            for index,name in enumerate(team_A):
                self.listWidget_A.addItem(name)
                if name in team_A_manual:
                    self.listWidget_A.item(index).setForeground(QtGui.QColor('red'))
            for index, name in enumerate(team_B):
                self.listWidget_B.addItem(name)
                if name in team_B_manual:
                    self.listWidget_B.item(index).setForeground(QtGui.QColor('blue'))

            self.new_rand_record()
            # 更新比赛次数和时间
            t=time.time()
            for j in self.join_list:
                self.name_dict[j]["random_times"] += 1
                self.name_dict[j]['last_time']=t
            write_json('name_list.json', self.name_dict)


    # 随机分多队
    def rand_teams(self):
        if not len(self.join_list):
            return False
        team_num=self.spinBox_2.value()
        #print(team_num)
        if len(self.join_list)%team_num!=0:
            self.error_label.setText('参赛人数无法整除预定队伍数')
        else:
            self.listWidget_teams.clear()
            player_count_of_team=int(len(self.join_list)/team_num)
            choosed_player_list=[]  #已经被选择的人
            for t in range(team_num):
                now_team= sample([i for i in self.join_list if i not in choosed_player_list], player_count_of_team)
                for i in now_team:
                    choosed_player_list.append(i)
                result_text = '第%d组：'%(t+1)
                for i in now_team:
                    result_text+=i+' '
                self.listWidget_teams.addItem(result_text)
            self.new_rand_record()
            # 更新比赛次数和时间
            t = time.time()
            for j in self.join_list:
                self.name_dict[j]["random_times"] += 1
                self.name_dict[j]['last_time'] = t
            write_json('name_list.json', self.name_dict)


    # 随机队长
    def rand_leader(self):
        if not len(self.join_list):
            return False
        self.listWidget_A.clear()
        self.listWidget_B.clear()

        team_A_manual, team_B_manual = [], []
        for index in range(self.join_listwidget.count()):
            if self.join_listwidget.item(index).foreground().color().getRgb() == (255, 0, 0, 255):
                team_A_manual.append(self.join_listwidget.item(index).text())
            elif self.join_listwidget.item(index).foreground().color().getRgb() == (0, 0, 255, 255):
                team_B_manual.append(self.join_listwidget.item(index).text())
        if len(team_A_manual) > int(len(self.join_list) / 2) or len(team_B_manual) > int(len(self.join_list) / 2):
            self.error_label.setText('手动添加的队伍人数\n超过队伍的一半，无法分队')
            return False
        # 红队剩余可选(所有人中除了手动蓝队的)
        red_remain_list=[i for i in self.join_list if i not in team_B_manual]
        blue_remain_list=[i for i in self.join_list if i not in team_A_manual]
        team_A = sample(red_remain_list, 1)
        team_B = sample([i for i in blue_remain_list if i not in team_A], 1)
        for index, name in enumerate(team_A):
            self.listWidget_A.addItem(name)
            if name in team_A_manual:
                self.listWidget_A.item(index).setForeground(QtGui.QColor('red'))
        for index, name in enumerate(team_B):
            self.listWidget_B.addItem(name)
            if name in team_B_manual:
                self.listWidget_B.item(index).setForeground(QtGui.QColor('blue'))
        self.new_rand_record()
        # 更新比赛次数和时间
        t = time.time()
        for j in self.join_list:
            self.name_dict[j]["random_times"] += 1
            self.name_dict[j]['last_time'] = t
        write_json('name_list.json', self.name_dict)

    # 手动增加红队|蓝队
    def team_manual_red_plus(self):
        if self.join_listwidget.currentItem() is None:
            return False
        self.join_listwidget.currentItem().setForeground(QtGui.QColor('red'))
    def team_manual_red_reduce(self):
        if self.join_listwidget.currentItem() is None:
            return False
        self.join_listwidget.currentItem().setForeground(QtGui.QColor('black'))
    def team_manual_blue_plus(self):
        if self.join_listwidget.currentItem() is None:
            return False
        self.join_listwidget.currentItem().setForeground(QtGui.QColor('blue'))
    def team_manual_blue_reduce(self):
        self.team_manual_red_reduce()

    '''随机装备区'''
    # 更新池的时候显示一些信息
    def when_pool_change(self):
        items_list=self.get_items_list()
        if not items_list:
            self.pool_items_count_label.setText('错误,详见下方错误信息')
            return False
        self.pool_items_count_label.setText('当前池共有%d件装备'%len(items_list))

    # 获取装备列表，每次随机装备要新存一下装备池名字
    def get_items_list(self):
        try:
            pool_name=False
            pool_name=self.comboBox_2.currentText()
            if pool_name in fixed_pool_dict:
                items_list=fixed_pool_dict[pool_name]
            else:
                items_list=read_txt_line(pool_name+'.txt')
            self.name_dict['init']['pn']=pool_name
            return items_list
        except:
            print(traceback.format_exc())
            self.error_label.setText('未找到%s.txt文件'%pool_name)
            return False

    # 随机装备列表
    def rand_items(self):
        items_list=self.get_items_list()
        if not items_list:return False
        items_num=self.spinBox.value()
        rand_items = sample(items_list, items_num)
        self.listWidget_item.clear()
        for i in rand_items:
            self.listWidget_item.addItem(i)
        self.new_rand_record()
        write_json('name_list.json', self.name_dict)

    # 为每个玩家随机一些装备
    def rand_items_for_each(self):
        if not len(self.join_list):return False
        items_list=self.get_items_list()
        if not items_list: return False
        items_num = self.spinBox_3.value()
        join_items_dict={}
        for j in self.join_list:
            join_items_dict[j]=[]
        for n in range(items_num):
            for j in self.join_list:
                item=sample(items_list,1)[0]
                join_items_dict[j].append(item)
                items_list.remove(item)
        self.listWidget_item.clear()
        for j,items in join_items_dict.items():
            self.listWidget_item.addItem('%s'%j)
            for i in items:
                self.listWidget_item.addItem(i)
        self.new_rand_record()
        write_json('name_list.json', self.name_dict)

    # 复制装备随机信息到粘贴板
    def copy_items_info(self):
        try:
            clipboard=QtWidgets.QApplication.clipboard()
            count = self.listWidget_item.count()
            weapon_icon_size = 20  # 图标压缩到多大
            line_height=int(weapon_icon_size*1.1) #行高
            total_width=weapon_icon_size*20
            img=QtGui.QImage(total_width,(count+3)*line_height,QtGui.QImage.Format_RGB32)
            img.fill(QtGui.QColor('white'))
            img_draw = QtGui.QPainter(img)
            # 字体像素大小px对应字号大小pt（磅）
            font_pt=int(weapon_icon_size/1.335)
            img_draw.setFont(QtGui.QFont('SimSun',font_pt))
            max_len=len(self.label_6.text().split()[0]) # 最长长度，最后用来截取
            for i in range(count):
                line_text=self.listWidget_item.item(i).text()
                line_len = len(line_text)+2
                if line_text in self.join_list:
                    # 玩家名加粗
                    img_draw.setFont(QtGui.QFont('SimSun', font_pt, QtGui.QFont.Bold))
                    team_A_list=[self.listWidget_A.item(i).text() for i in range(self.listWidget_A.count())]
                    team_B_list = [self.listWidget_B.item(i).text() for i in range(self.listWidget_B.count())]
                    if self.listWidget_item.item(i).text() in team_A_list:
                        img_draw.setPen(QtGui.QColor('red'))
                    elif self.listWidget_item.item(i).text() in team_B_list:
                        img_draw.setPen(QtGui.QColor(0,100,255,255))
                    else:
                        img_draw.setPen(QtGui.QColor('green'))
                    img_draw.drawText(int(weapon_icon_size*2.1), (i + 1) * line_height, line_text)

                else:
                    img_draw.setFont(QtGui.QFont('SimSun', font_pt))
                    img_draw.setPen(QtGui.QColor('black'))
                    img_draw.drawText(int(weapon_icon_size*1.1), (i + 1) * line_height, line_text)
                    # 获取图标并且输出
                    icon,now_name=get_weapon_prc_icon(line_text)
                    if icon:
                        if now_name:
                            img_draw.drawText(int(weapon_icon_size * (1 + len(line_text))), (i + 1) * line_height,'(' + now_name + ')')
                            line_len+=len(now_name)
                        icon.scaledToWidth(weapon_icon_size)
                        img_draw.drawPixmap(0, i * line_height + 5, weapon_icon_size, weapon_icon_size, icon)
                if line_len>max_len:
                    max_len=line_len

            img_draw.setPen(QtGui.QColor('orange'))
            img_draw.drawText(5, (count+1) * line_height, self.label_6.text().split()[0])
            img_draw.drawText(5, (count + 2) * line_height, self.name_dict['init']['pn'])
            img_draw.drawText(5, (count + 3) * line_height, sft())
            del img_draw
            qimg=QtGui.QPixmap(img.copy(0,0,max_len*line_height,(count+3)*line_height))
            clipboard.setPixmap(qimg)
            del img
            del qimg
        except:
            print(traceback.format_exc())

    # 刷新装备池文件
    def renew_pools(self):
        add_pool_list=[]    # 附加装备池表，和固定在程序里的加以区分
        self.comboBox_2.clear()
        for i in os.listdir():
            if '.txt' in i:
                pool_name=i.replace('.txt','')
                if pool_name not in fixed_pool_dict:
                    add_pool_list.append(pool_name)
        self.comboBox_2.addItem(self.name_dict['init']['pn'])
        for pool_name in fixed_pool_dict:
            if pool_name!=self.name_dict['init']['pn']:
                self.comboBox_2.addItem(pool_name)
        for pool_name in add_pool_list:
            if pool_name != self.name_dict['init']['pn']:
                self.comboBox_2.addItem(pool_name)

    # 调用新窗口,显示当前池内所有装备
    def show_pool_items(self):
        pool_name = self.comboBox_2.currentText()
        self.pool_show.Open(pool_name,self.get_items_list())


    '''手动记录区'''

    # 打开/关闭手动计数区
    def manual_open(self):
        if not self.manual_area:
            self.manual_area=True
            self.resize(self.width(),self.height()+260)
        else:
            self.manual_area = False
            self.resize(self.width(), self.height() - 260)

    # 复制参赛列表到手动计数区
    def copy_join(self):
        # 只有当参赛列表、随机分队有人时，且计数列表为空时，才可以复制，
        if not len(self.join_list) or not self.listWidget_A.count() or self.manual_listWidget.count():
            self.error_label.setText('参赛列表为空|未随机分队|计数区非空')
            return False
        self.manual_clear()
        for index,name in enumerate(self.join_list):
            self.manual_list.append(name)
            self.manual_listWidget.addItem(name)
            color = QtGui.QColor(self.manual_color[index][0], self.manual_color[index][1],
                                 self.manual_color[index][2], self.manual_color[index][3])
            self.manual_listWidget.item(index).setForeground(color)


    # 清空手动记录
    def manual_clear(self):
        self.manual_record.clear()
        self.manual_total_record.clear()
        self.manual_listWidget.clear()
        self.manual_list.clear()
        self.manual_addnsub=[0 for i in range(12)]
        for l in self.manual_labels:
            l.setText('')

    # 手动记录-红队胜利
    def manual_red_win(self):
        if not self.manual_listWidget.count():
            return False
        # 临时记录本次结果，后续放入记录中。同当前队伍信息对比，输了-1，赢了+1
        temp_record=[0 for i in range(12)]
        for i in range(self.listWidget_A.count()):
            team_name=self.listWidget_A.item(i).text()
            for index,name in enumerate(self.manual_list):
                if team_name==name:
                    temp_record[index]+=1
        for i in range(self.listWidget_B.count()):
            team_name=self.listWidget_B.item(i).text()
            for index,name in enumerate(self.manual_list):
                if team_name==name:
                    temp_record[index]-=1
        self.manual_new_record(temp_record)
        self.manual_show_record()

    # 手动记录-蓝队胜利
    def manual_blue_win(self):
        if not self.manual_listWidget.count():
            return False
        # 临时记录本次结果，后续放入记录中。同当前队伍信息对比，输了-1，赢了+1
        temp_record = [0 for i in range(12)]
        for i in range(self.listWidget_A.count()):
            team_name = self.listWidget_A.item(i).text()
            for index, name in enumerate(self.manual_list):
                if team_name == name:
                    temp_record[index] -= 1
        for i in range(self.listWidget_B.count()):
            team_name = self.listWidget_B.item(i).text()
            for index, name in enumerate(self.manual_list):
                if team_name == name:
                    temp_record[index] += 1
        self.manual_new_record(temp_record)
        self.manual_show_record()

    # 放入新纪录(只有当此时将全部记录和当前记录同步)
    def manual_new_record(self,temp_record):
        self.manual_record.append(temp_record)
        self.manual_total_record.clear()
        for i in self.manual_record:
            self.manual_total_record.append(i)

    # 显示记录在label中
    def manual_show_record(self):
        for l in self.manual_labels:
            l.setText('')
        temp_text=''
        for times in range(len(self.manual_record)):
            temp_text+='第%d局\t'%(times+1)
        self.manual_labels[0].setText(temp_text+'补充项\t汇总')
        for index in range(1,13):
            if index >len(self.manual_list):
                break
            sum=0
            temp_text = ''
            for record in self.manual_record:
                temp_text+='%s\t'%record[index-1]
                sum+=record[index-1]
            sum+=self.manual_addnsub[index-1]
            self.manual_labels[index].setText(temp_text+'%d\t%d'%(self.manual_addnsub[index-1],sum*self.manual_spinBox.value()))

    # 撤销一步手工记录
    def manual_undo(self):
        if not len(self.manual_record):
            return False
        del self.manual_record[-1]
        self.manual_show_record()
    # 恢复一步手工记录
    def manual_recover(self):
        if len(self.manual_record) >= len(self.manual_total_record):
            return False
        self.manual_record.append(self.manual_total_record[len(self.manual_record)])
        self.manual_show_record()

    # 判断手动补充是否平衡(输赢数量和为零)
    def manual_addnsub_update(self):
        if sum(self.manual_addnsub)!=0:
            self.error_label.setText('手动补充项错误！\n请注意输赢数和应为0')
        else:
            self.error_label.setText('')

    # 手动补充添加
    def manual_add(self):
        if self.name_listwidget.currentItem() is None:
            return False
        indexs=self.manual_listWidget.selectedIndexes()
        for index in indexs:
            self.manual_addnsub[index.row()]+=1
        self.manual_addnsub_update()
        self.manual_show_record()
    # 手动补充删除
    def manual_sub(self):
        if self.name_listwidget.currentItem() is None:
            return False
        indexs = self.manual_listWidget.selectedIndexes()
        for index in indexs:
            self.manual_addnsub[index.row()] -= 1
        self.manual_addnsub_update()
        self.manual_show_record()

    # 复制手工计数输出成图片
    def manual_copy(self):
        clipboard = QtWidgets.QApplication.clipboard()
        player_count = len(self.manual_list)
        match_count=len(self.manual_record)
        img = QtGui.QImage(60+(match_count+2)*40, (player_count+1) * 14+6, QtGui.QImage.Format_RGB32)
        img.fill(QtGui.QColor('white'))
        img_draw = QtGui.QPainter(img)
        # 输出标题
        img_draw.drawText(100, 14, '补充项')
        img_draw.drawText(60 , 14, '汇总')
        for ri,r in enumerate(self.manual_record):
            img_draw.drawText(60 + ((ri+2) * 40), 14, '第%d局'%(ri+1))
        # i是玩家序号
        for i in range(player_count):
            color = QtGui.QColor(self.manual_color[i][0], self.manual_color[i][1],self.manual_color[i][2], self.manual_color[i][3])
            img_draw.setPen(color)
            img_draw.drawText(5, (i + 2) * 14, self.manual_list[i])
            sum = 0
            for record in self.manual_record:
                sum += record[i]
            img_draw.drawText(60 , (i + 2) * 14, str((sum+self.manual_addnsub[i])*self.manual_spinBox.value()))
            img_draw.drawText(100, (i + 2) * 14, str(self.manual_addnsub[i]))
            # ri是比赛序号，r是单次比赛的记录
            for ri,r in enumerate(self.manual_record):
                img_draw.drawText(60 + ((ri+2) * 40), (i + 2) * 14, str(r[i]))
        del img_draw
        qimg = QtGui.QPixmap(img)
        clipboard.setPixmap(qimg)

if __name__ =='__main__':
    '''初始化'''
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)  # 适应高DPI设备
    QtGui.QGuiApplication.setAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)  # 适应windows缩放
    app = QtWidgets.QApplication(sys.argv)
    Main = MainWindow()
    Main.show()
    sys.exit(app.exec())
