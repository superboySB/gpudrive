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
NOTE: If you downloaded the full-sized dataset, it is grouped to subdirectories of 10k files each (according to hugging face constraints). In order for the path to work with GPUDrive, you need to run
```sh
python data_utils/postprocessing.py
```
跟着所有ipynb走一遍吧。

### 内部网络（todo）