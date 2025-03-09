# default: png -> webp
for file in *.png; do
    ffmpeg -i "$file" "${file%.png}.webp"
done


# # r2q5 (ARCAEA): quality = 10%, wh = 33% (=1280x800)
# for file in r2q5*.png; do
#     ffmpeg -i "$file" -vf scale=1280:800 -qscale:v 10 "${file%.png}.webp"
# done


# # r2q2 (AREA): quality = 1%, wh = 25%
# for file in r2q2*.png; do
#     ffmpeg -i "$file" -vf "scale=iw/4:ih/4" -qscale:v 1 "${file%.png}.webp"
# done