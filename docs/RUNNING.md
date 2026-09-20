# 실행과 조작

## 필요한 로컬 구성

이 저장소에는 USD와 학습 가중치가 없다. 기존 SpotATS_ws 로컬 작업 공간의 `training`, `runtime`, `assets`, 정책과 원본 자산이 필요하다. upstream 저장소만 새로 복제한 상태에는 로컬 학습·통합 모듈이 모두 포함되어 있지 않을 수 있다. 실행기는 파일 경로를 환경 변수로 전달받으며, 원본 디렉터리를 수정하지 않는다.

실행 검증 환경은 Ubuntu, ROS 2 Humble, Isaac Sim 5.0 계열과 Isaac Lab이다. Isaac은 Python 3.11, 시스템 ROS는 Python 3.10을 사용한다. 예제의 DDS 도메인은 91이다. 다른 로봇과 같은 도메인을 사용하지 않도록 실행 환경에 맞춰 설정한다.

```bash
export SPOTATS_WORKSPACE=/path/to/your/SpotATS_ws
export ISAACLAB_ROOT=/path/to/IsaacLab
export ISAAC_PYTHON=/path/to/isaac/environment/bin/python
export ROS_DOMAIN_ID=91
```

## 물리 모델과 센서 실행

```bash
bash scripts/run_unified.sh --headless --capture --rgbd \
  --mode walk --duration 8 --output ../evidence/walk
```

| 옵션 | 조작 의미 |
|---|---|
| `--mode walk` | 전진 0.3m/s를 요청하여 보행 정책을 확인한다 |
| `--mode ats` | 정지 보행 상태에서 두 ATS 관절의 제한 내 동작을 확인한다 |
| `--mode perception` | 검증용 인물을 전방 3m에 배치한 통제 장면을 실행한다 |
| `--mode ros` | ROS 2 `/cmd_vel`의 명령을 사용한다 |
| `--duration` | 목표 시뮬레이션 시간이다. 촬영으로 실제 소요 시간은 길어진다 |
| `--capture` | 외부 관찰 카메라로 실제 프레임을 기록한다 |
| `--rgbd` | 로봇 탑재 관측 위치의 RGB·깊이 영상을 발행·기록한다 |
| `--output` | 로컬 원본 프레임·깊이 배열·상태 기록 저장 위치이다 |

`/ats_twist`의 `angular.z`, `angular.y`는 각각 두 ATS 관절의 목표각 변화율로 사용한다. 실행기는 초당 최대 ±0.6rad의 변화율과 로드된 관절 제한을 적용한다. 0.5초 동안 새 ATS 명령이 없으면 마지막 목표각을 유지한다. 이는 기구 제어 통합 확인용이며, 인식에서 ATS까지의 폐루프 추적 성능을 입증하는 시험과는 구별한다.

## Nav2와 RViz

별도 시스템 ROS 터미널에서 다음을 실행한다.

```bash
bash scripts/run_nav_demo.sh
```

이후 Isaac 터미널에서 `--mode ros`를 실행한다. 예제는 odom 좌표의 `(2.0, 0.5)`를 목표로 요청한다. RViz는 2D 스캔, 3D 포인트클라우드, 경로, 실제 오도메트리와 TF를 표시한다. 예제는 센서 기반 국소 지도와 시뮬레이터 오도메트리를 사용하는 제한된 이동 시험이다. AMCL 전역 위치추정이나 전체 창고 순찰 성공을 대신하는 시험은 아니다.

Nav2 설정은 설치된 기본 YAML을 바탕으로 `prepare_nav.py`가 생성한다. 시뮬레이션 시간, body 프레임, 보행 가능한 속도, 경로 추종기와 장애물 관측을 명시한다. 원본의 일부 설정에 함께 켜져 있던 `use_rotate_to_heading`과 `allow_reversing`은 여기서 각각 true와 false로 선택한다.

## 영상과 문서 재생성

```bash
"$ISAAC_PYTHON" scripts/perception_replay.py
"$ISAAC_PYTHON" scripts/build_media.py
"$ISAAC_PYTHON" scripts/build_figures.py
```

YOLO 재생은 신뢰하는 로컬 체크포인트를 사용하여 기록된 RGB 프레임에 실제 추론을 수행한다. 실시간 통합 성능 측정과는 구별한다. MP4는 H.264·yuv420p·faststart를 사용하며, README에는 GIF를 직접 삽입한다.

## 통신 설정 근거

두 실행 환경에서 동일한 `config/fastdds.xml`을 사용한다. 이는 UDP 전송을 명시하는 구성이다. 적용 방식은 [NVIDIA Isaac Sim 5.0 ROS 설치 문서](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/installation/install_ros.html)를 참고한다. 적용 효과는 해당 실행 결과로 확인하며, 이전 통신 지연의 원인이 공유 메모리였다고 단정하지 않는다.
