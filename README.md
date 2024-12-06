conda env list
conda remove -n chanpy --all
conda config --show channels
conda config --remove channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/pro/
conda config --remove channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch/
conda config --remove channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
conda config --remove channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/

$env:all_proxy=""
$env:http_proxy= ""
$env:https_proxy= ""
$env:all_proxy="socks5://127.0.0.1:10808"
$env:http_proxy= "http://127.0.0.1:10808"
$env:https_proxy= "https://127.0.0.1:10808"
$env:CONDA_FORCE_32BIT=1

set http_proxy=socks5://127.0.0.1:10808
set https_proxy=socks5://127.0.0.1:10808

Invoke-WebRequest -Uri "https://www.google.com"

conda create -n chanpy python=3.8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='gb18030') 

conda create -n chanpy
conda create -n ixshare
conda env list
conda activate chanpy
D:\anaconda3\envs\chanpy\Scripts\pip install akshare --upgrade
D:\anaconda3\envs\ixshare\Scripts\pip install akshare --upgrade
conda config --add channels conda-forge
conda install mplfinance    conda install -c conda-forge mplfinance
conda install requests

pip freeze > requirements.txt
