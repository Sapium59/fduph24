# default: png -> webp
# for file in *.png; do
#     ffmpeg -i "$file" "${file%.png}.webp"
# done


# r2q5 (ARCAEA): quality = 10%, wh = 33% (=1280x800)
for file in r2q5-15*.png; do
    ffmpeg -i "$file" -vf scale=1280:800 -qscale:v 10 "${file%.png}.webp"
done


# # r2q2 (AREA): quality = 50%
# for file in r2q2-07*.png; do
#     # mv $file "${file%.png}.25.1.webp"
#     ffmpeg -i "$file" -qscale:v 50 "${file%.png}.webp"
# done