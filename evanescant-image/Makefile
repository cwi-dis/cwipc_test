# getReleaseFromGitlab
gRFG=../../Deployment/getReleaseFromGitLab
# evanescent binary after getting it from gitlab release
evanescent=tmp/installed/gnu/evanescent.exe

all: $(evanescent)
	docker build -t ubuntu1804-vrtogether-evanescent .
	
$(evanescent):
	python3 $(gRFG) --noverify --curdir
	rm -rf tmp
	mkdir tmp
	(cd tmp &&  unzip ../evanescent-*.zip)
	
install: all
	docker tag ubuntu1804-vrtogether-evanescent jackjansen/ubuntu1804-vrtogether-evanescent
	docker push jackjansen/ubuntu1804-vrtogether-evanescent:latest
 
