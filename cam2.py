from common_import import *
import threading
import time
import socket
import select
from my_rx_buf import my_rx_buf
from common_type_def import *
from rx_general_data_multi_thread import rx_general_data_multi_thread

def main(endtime=20):
  # User Option
  ip = '127.0.0.1'
  port = 7168
  rx_data_type = camera_for_crosswalk
  save_parsed_data = True

  rx_obj = rx_general_data_multi_thread(
    save_parsed_data = save_parsed_data)
  rx_obj.init(ip, port, rx_data_type)
  rx_obj.start_thread_func()

  # Timer를 초기화
  t_offset = time.time()
  t_last_loop = time.time() - t_offset

  # 제어 루프 속도
  # [주의 사항] control_freq는 너무 낮거나, 너무 높으면 안 된다.
  # 1) 해당 SW 실행 시 Buffer에 Write를 못한다는 Warning이 지속적으로 발생하면
  #    control_freq가 너무 낮은 것임. 이 때는 control_freq를 올려야 함
  # 2) control_freq는 시뮬레이터의 FPS값보다 낮게 주어야 한다.
  #    이 값을 너무 높이면 시뮬레이터가 전송된 명령을 제대로 처리하지 못할 수 있음
  #    (데모 버전 시뮬레이터 내 버퍼 관련 이슈임)
  control_freq = 25
  control_period = 1/control_freq

  try:
    cnt = 0
    while True:
      # 현재 시각을 측정하고 종료할 시간이 되면 종료한다
      t = time.time() - t_offset
      if t > endtime:
        break

      # 제어 루프를 다시 실행할 시간이 될 때 까지 polling한다
      diff_t = t - t_last_loop
      if diff_t < control_period:
        continue

      # [제어 루프 시작] 현재 시각 저장 (다음 제어 루프 실행을 위해 필요)
      cnt += 1
      t_last_loop = t

      # 데이터 읽기
      data = rx_obj.get_buf().read_nonblocking()
      if data != None:
          if save_parsed_data:
            print('[Main  ] [TRACE] {} {}'.format(cnt, data.to_string()))
          else:
            parsed_data = rx_data_type.create_object_from_bytes_data(data)
            print('[Main  ] [TRACE] {} {}'.format(cnt, parsed_data.to_string()))

      if not rx_obj.is_thread_func_ok():
        print('[Main  ] [WARN] Error is detected from another thread')
        break

  except KeyboardInterrupt as e:
    print("[Main  ] [INFO] Terminated by KeyboardInterrupt")
    rx_obj.signal_thread_func_to_stop()

  # Clean out before exit
  print("[Main  ] [INFO] Trying to close threads...")
  rx_obj.signal_thread_func_to_stop()
  rx_obj.get_thread_handle().join(timeout=10.0)
  print("[Main  ] [INFO] Exiting the main program")

  if rx_obj.get_thread_handle().is_alive():
    print("[Main  ] [WARN] A child thread is not closing properly.")

  return


if __name__ == '__main__':
  main()
