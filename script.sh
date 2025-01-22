cd ./templates
file=$(find . -type f -not -path "./helper_scripts/*" -not -path "./source_code/*" | rofi -dmenu -i -p "Template")
esh "$file" | perl -pe 'chomp if eof' | ${OP_COPY_COMMAND:-xclip}
