# 复现笔记
## 配置
```sh
DOCKER_BUILDKIT=1 docker build --build-arg USE_CUDA=true --network host --tag dzp_waymax:0717 --progress=plain .

docker run -itd --privileged --gpus all --net=host -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro --shm-size=20G \
  -v /home/dzp/Downloads/for_waymax/GPUDrive_mini:/workspace/dataset/ \
  --name dzp-waymax-0717 dzp_waymax:0717 /bin/bash

python data_utils/postprocessing.py
```