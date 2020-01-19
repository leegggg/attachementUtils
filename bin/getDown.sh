#!/usr/bin/env bash
if [[ -z $1 ]]; then
    echo "kw needed"
    exit
fi

tag=tieba_img
if test -z "$2" 
then
    echo "$2 is empty"
else
    echo "$2 is NOT empty"
    tag=$2
fi

cd /home/ylin/attachementUtils/
source env/bin/activate
systemd-cat -t $tag python ./attachementUtils/attachementUtil.py -d sqlite:////home/ylin/anna/ext_hdd/by-uuid/aea3c7d1-7bf3-4028-a87f-b9dc140a6eec/all.$1.tieba.baidu.com.db -p /home/ylin/anna/ext_hdd/by-uuid/aea3c7d1-7bf3-4028-a87f-b9dc140a6eec/$1IMG/