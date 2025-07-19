# 复现笔记
## 配置
### 外部网络
```sh
DOCKER_BUILDKIT=1 docker build --build-arg USE_CUDA=true --network host --tag dzp_waymax:0717 --progress=plain .

docker run -itd --privileged --gpus all --net=host -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro --shm-size=20G \
  -v /home/dzp/Downloads/for_waymax:/workspace/for_waymax/ \
  --name dzp-waymax-0717 dzp_waymax:0717 /bin/bash

docker exec -it dzp-waymax-0717 /bin/bash
```
跟着所有ipynb走一遍吧，注意GTX 1050 Ti 计算能力是 6.1，但 madrona_gpudrive 需要计算能力 7.0+ 的 CUDA 功能，在小破本上会导致编译失败并回退到 CPU 模式，device设置失效。
```sh
CUDA_VISIBLE_DEVICES=0 python baselines/ppo/ppo_sb3.py
```
目前Pufferlib缺少了同步维护，后续可以看一下怎么结合现有SB3或者cleanRL。

### 内部网络
注意挂个硬盘，还有内部不能用wandb
```sh
docker run -itd --privileged --gpus all --net=host -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro --shm-size=20G \
  -v /disk:/disk -v /disk1:/disk1 -v /mnt:/mnt \
  --name dzp-waymax-0717 dzp_waymax:0717 /bin/bash
```
NOTE: If you downloaded the full-sized dataset, it is grouped to subdirectories of 10k files each (according to hugging face constraints). In order for the path to work with GPUDrive, you need to run
```sh
# mini version
# python data_utils/post_processing.py /workspace/for_waymax/GPUDrive_mini --target_dir data/processed --num_workers 8
python data_utils/post_processing.py /disk/deepdata/dataset/GPUDrive --target_dir data/processed --num_workers 64
```
尝试跑大的
```sh
CUDA_VISIBLE_DEVICES=0 python baselines/ppo/ppo_sb3.py --config baselines/ppo/config/ppo_train_full_0719.yaml
```

## 定制化开发
### 注意！修改MDP建模后需要重新编译
```sh
bash rebuild.sh
```
### 魔改Corner Case

