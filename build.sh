# to build execfile
# yum install -y python3-devel

rm -fr dist/inpanel
rm -fr build/

pyinstaller -y --noconfirm inpanel.spec
