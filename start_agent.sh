#!/bin/bash
# 创建启动脚本：start_agent.sh

gnome-terminal -- bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate gewe && python /home/ycy/Code/Agent-with-wechat/Agent_hall.py; exec bash"