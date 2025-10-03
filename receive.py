from pylsl import StreamInlet, resolve_stream

# 1. ストリームの検索（typeが "XYCoordinates" のもの）
print("LSLストリームを検索中...")
# streams = resolve_stream('type', 'XYCoordinates')
streams = resolve_stream('type', 'gaze')  # ← 小文字の 'gaze' に注意！


# 2. 最初に見つかったストリームに接続
inlet = StreamInlet(streams[0])
print("ストリームに接続しました！")

# 3. サンプルを連続して受信
try:
    while True:
        sample, timestamp = inlet.pull_sample()
        x = (sample[0] +sample[6])/2
        y = (sample[1] + sample[7])/2

        print(f"receive:{x}, {y} ")
except KeyboardInterrupt:
    print("終了しました")
