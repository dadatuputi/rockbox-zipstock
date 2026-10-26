# helpers: start | key NAME [n] | shot NAME | stop
export DISPLAY=:99
B=${RB_SIM:-$HOME/rb/bs}   # a Rockbox simulator build dir (configure --target=sansaclipzip --type=s)
SHOTS=${SHOTS:-$PWD/shots}
case $1 in
start)
  pgrep Xvfb >/dev/null || (Xvfb :99 -screen 0 640x480x24 >/dev/null 2>&1 &)
  sleep 1
  cd $B && (SDL_AUDIODRIVER=dummy ./rockboxui --nobackground --debugwps > $B/sim.log 2>&1 &)
  sleep 6 ;;
key)
  n=${3:-1}; for i in $(seq $n); do W=$(xdotool search --name "Sansa Clip Zip" | head -1); xdotool windowfocus $W 2>/dev/null; xdotool keydown --window $W $2; sleep 0.12; xdotool keyup --window $W $2; sleep 0.6; done ;;
shot)
  rm -f $B/simdisk/dump*.bmp; W=$(xdotool search --name "Sansa Clip Zip" | head -1); xdotool windowfocus $W; xdotool key --window $W F5; sleep 1.2
  f=$(ls -t $B/simdisk/dump*.bmp 2>/dev/null | head -1); mkdir -p $SHOTS
  [ -n "$f" ] && mv "$f" $SHOTS/$2.bmp && echo saved $2 || echo "no dump" ;;
stop)
  pkill rockboxui; sleep 1 ;;
esac
