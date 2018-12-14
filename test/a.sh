#!/bin/bash
#在使用程序前请务必茶看下面的cron计划任务的大体书写格式，
#当然我编写本程序限定了输入格式，错误的输入不会写入:
 
# 详细的信息请使用 man 4 crontabs 命令:
 
# Example of job definition:
# .---------------- minute (0 - 59) #这里格式还可以指定 */10 的格式
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed

#[CODE START]

#命名计划任务:

CRON_DIR=/etc/cron.d/
read -p "创建计划任务名称:" cronname
CRON_NAME=$cronname
CRON_FILE=$CRON_DIR$CRON_NAME
echo "将创建 $CRON_FILE 文件,正在检查任务名称是否存在..."

#判断计划任务要创建的文件是否存在:

ls $CRON_FILE &> /dev/null

#文件存在后的操作:

while [ $? = 0 ];do
	read -p "计划任务名称已经存在,是否进行追加操作(输入yes or no)?" choice
	if [ $choice = "yes" ];then
		break
	elif [ $choice = "no" ];then
		read -p "请重新输入计划任务名称:" cronname
		CRON_NAME=$cronname
		CRON_FILE=$CRON_DIR$CRON_NAME
		ls $CRON_FILE &> /dev/null
	else
		echo "选择不正确"
		ls $CRON_FILE &> /dev/null
	fi
done

#创建计划任务文件:

touch $CRON_FILE

str1=''
#判断分钟值的格式正确性:
while [ -z $str1  ];do
	read -p "请输入分钟:" cron_min
	if [ -z "$cron_min" ];then
		cron_min="*"
		break
	fi
	num=$(echo $cron_min | wc -L)
	if [ $num -eq 1 ];then
		str1=$(echo $cron_min | grep ^[0-9,*])
	elif [ $num -eq 2 ];then
		str1=$(echo $cron_min | grep ^[1-5,/][0-9])
		echo $cron_min | grep ^[/] &>/dev/null
		if [ $? = 0 ];then
			cron_min="*"$str1
		fi
	elif [ $num -eq 3 ];then
		echo $cron_min | grep ^[/] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_min | grep ^[/][1-5][0-9])
			cron_min="*"$str1
		else
			str1=$(echo $cron_min | grep ^[0-9][-][0-9])
		fi
	elif [ $num -eq 4 ];then
		str1=$(echo $cron_min | grep ^[0-9][-][1-5][0-9])
	elif [ $num -eq 5 ];then
		str1=$(echo $cron_min | grep ^[1-5][0-9][-][1-5][0-9])
	else
		echo "输入的格式不正确,正确格式有:1-2 \| /10 \| /1 \| * \| 1-12 \| 35-59 等"
		str1=''
	fi
done

echo "cron_min:"$cron_min

#判断小时值的正确性:
str1=''
while [ -z $str1  ];do
	read -p "请输入小时:" cron_hour
	if [ -z "$cron_hour" ];then
		cron_hour="*"
		break
	fi
	num=$(echo $cron_hour | wc -L)
	if [ $num -eq 1 ];then
		str1=$(echo $cron_hour | grep ^[0-9,*])
	elif [ $num -eq 2 ];then
		str1=$(echo $cron_hour | grep ^[0-1,/][0-9])
		echo $cron_hour | grep ^[/] &>/dev/null
		if [ $? = 0 ];then
			cron_hour="*"$str1
		fi
		echo $cron_hour | grep ^[2] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_hour | grep ^[2][0-4])
		fi
	elif [ $num -eq 3 ];then
		echo $cron_hour | grep ^[/] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_hour | grep ^[/][0-1][0-9])
			cron_hour="*"$str1
		else
			str1=$(echo $cron_hour | grep ^[0-9][-][0-9])
		fi
		echo $cron_hour | grep ^[/][2] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_hour | grep ^[/][2][0-4])
		fi
	elif [ $num -eq 4 ];then
		str1=$(echo $cron_hour | grep ^[0-9][-][1][0-9])
		echo $cron_hour | grep ^[0-9][-][2] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_hour | grep ^[0-9][-][2][0-4])
		fi
	elif [ $num -eq 5 ];then
		str1=$(echo $cron_hour | grep ^[1][0-9][-][1][0-9])
		echo $cron_hour | grep ^[1][0-9][-][2]
		if [ $? = 0 ];then
			str1=$(echo $cron_hour | grep ^[1][0-9][-][2][0-4])
		fi
		echo $cron_hour | grep ^[2]
		if [ $? = 0 ];then
			str1=$(echo $cron_hour | grep ^[2][0-4][-][2][0-4])
		fi
		
	else
		echo "输入的格式不正确,正确格式有:1-2 \| /10 \| /1 \| * \| 1-12 \| 10-23 等"
		str1=''
	fi
done
 
 
echo "cron_hour:"$cron_hour
 
#判断天数值的正确性:
str1=''
while [ -z $str1  ];do
	read -p "请输入天数:" cron_day
	if [ -z "$cron_day" ];then
		cron_day="*"
		break
	fi
	num=$(echo $cron_day | wc -L)
	if [ $num -eq 1 ];then
		str1=$(echo $cron_day | grep ^[1-9,*])
	elif [ $num -eq 2 ];then
		str1=$(echo $cron_day | grep ^[0-2,/][0-9])
		echo $cron_day | grep ^[/] &>/dev/null
		if [ $? = 0 ];then
			cron_day="*"$str1
		fi
		echo $cron_day | grep ^[3] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_day | grep [3][0-1])
		fi
	elif [ $num -eq 3 ];then
		echo $cron_day | grep ^[/] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_day | grep ^[/][1-2][0-9])
			cron_day="*"$str1
		else
			str1=$(echo $cron_day | grep ^[1-9][-][1-9])
		fi
		echo $cron_day | grep ^[/][3] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_day | grep ^[/][3][0-1])
		fi
	elif [ $num -eq 4 ];then
		str1=$(echo $cron_day | grep ^[1-9][-][1-2][0-9])
		echo $cron_day | grep ^[1-9][-][3] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_day | grep [1-9][-][3][0-1])
		fi
	elif [ $num -eq 5 ];then
		str1=$(echo $cron_day | grep ^[1-2][0-9][-][1-2][0-9])
		echo $cron_day | grep ^[1-2][0-9][-][3]
		if [ $? = 0 ];then
			str1=$(echo $cron_day | grep ^[1-2][0-9][-][3][0-1])
		fi
		echo $cron_day | grep ^[3]
		if [ $? = 0 ];then
			str1=$(echo $cron_day | grep ^[3][0-1][-][3][0-1])
		fi
	else
		echo "输入的格式不正确,正确格式有:1-2 \| /10 \| /1 \| * \| 1-12 \| 18-28 等"
		str1=''
	fi
done
 
echo "cron_day:"$cron_day
 
#判断月份值的正确性:
str1=''
while [ -z $str1  ];do
	read -p "请输入月份:" cron_mon
	if [ -z "$cron_mon" ];then
		cron_mon="*"
		break
	fi
	num=$(echo $cron_mon | wc -L)
	if [ $num -eq 1 ];then
		str1=$(echo $cron_mon | grep ^[1-9,*])
	elif [ $num -eq 2 ];then
		str1=$(echo $cron_mon | grep ^[1,/][1-9])
		echo $cron_mon | grep ^[/] &>/dev/null
		if [ $? = 0 ];then
			cron_mon="*"$str1
		fi
		echo $cron_mon | grep ^[1] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_mon | grep ^[1][0-2])
		fi
	elif [ $num -eq 3 ];then
		echo $cron_mon | grep ^[/] &>/dev/null
		if [ $? = 0 ];then
			str1=$(echo $cron_mon | grep ^[/][1][0-2])
			cron_mon="*"$str1
		else
			str1=$(echo $cron_mon | grep ^[1-9][-][1-9])
		fi
	elif [ $num -eq 4 ];then
		str1=$(echo $cron_mon | grep ^[1-9][-][1][0-2])
	elif [ $num -eq 5 ];then
		str1=$(echo $cron_mon | grep ^[1][0-2][-][1][0-2])
	else
		echo "输入的格式不正确,正确格式有:1-2 \| 12 \| /10 \| /1 \| * \| 1-12 \| 10-11 等"
		str1=''
	fi
done
 
echo "cron_mon:"$cron_mon
 
#day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
echo "请输入星期(输入0-7任意一个数,1-6为星期一～星期六|星期日请输入0或7)"

str1=''
while [ -z $str1 ];do
	read -p "输入:" cron_week
	num=$(echo $cron_week | wc -L)
	if [ $num -eq 0 ];then
		cron_week="*"
		break
	elif [ $num -eq 1 ];then
		str1=$(echo $cron_week | grep ^[0-7,*])
		echo $cron_week | grep ^[0-7,*]
		if [ $? = 1 ];then
			echo "输入了不存在的星期,请重新输入"
		fi
	else
		echo "输入不正确,(输入0-7任意一个数,1-6为星期一～星期六|星期日请输入0或7),回车默认为*"
	fi
done
echo "cron_week:"$cron_week

str1=''

while [ -z $str1 ];do
	read -p "请输入用户名:" cron_user
	if [ -z $cron_user ];then
		break
	fi
	id $cron_user
	if [ $? = 0 ];then
		str1=$cron_user
	else
		echo "本地用户名不存在,请核对后再输入!"
	fi
done
 
str1=''
while [ -z "$str1" ];do
	read -p "请输入命令:" cron_cmnd
	if [ -z "$cron_cmnd" ];then
		echo "没有输入命令!"
	else
		str1=$cron_cmnd
	fi
done
 
echo "您的计划任务详细条目为:"
echo "$CRON_FILE:"
if [ -z "$cron_user" ];then
	echo "$cron_min $cron_hour $cron_day $cron_mon $cron_week $USER $cron_cmnd"
else
	echo "$cron_min $cron_hour $cron_day $cron_mon $cron_week $cron_user $cron_cmnd"
fi
 
str1=''
while [ -z $str1 ];do
	read -p "确认创建计划任务么(Y/n)" yesno
	if [ "$yesno" = "Y" ];then
		if [ "$choice" = "yes" ];then
			if [ -z "$cron_user" ];then 
				echo "$cron_min $cron_hour $cron_day $cron_mon $cron_week $USER $cron_cmnd" >> $CRON_FILE
			else
				echo "$cron_min $cron_hour $cron_day $cron_mon $cron_week $cron_user $cron_cmnd" >> $CRON_FILE
			fi
			break
		else
			if [ -z "$cron_user" ];then
				echo "$cron_min $cron_hour $cron_day $cron_mon $cron_week $USER $cron_cmnd" > $CRON_FILE
			else
					
				echo "$cron_min $cron_hour $cron_day $cron_mon $cron_week $cron_user $cron_cmnd" > $CRON_FILE
			fi
			break
		fi
	elif [ "$yesno" = "n" ];then
		break
	else 
		str1=''
	fi
done
 
echo "计划任务创建成功"
#[CODE END]
