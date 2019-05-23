# getReleaseFromGitlab
gRFG=../../Deployment/getReleaseFromGitLab
# evanescent binary after getting it from gitlab release
evanescent=tmp/installed/gnu/evanescent.exe

all: $(evanescent)
	docker build -t ubuntu1804-vrtogether-evanescent .
	
$(evanescent):
	REQUESTS_CA_BUNDLE="" python3 $(gRFG) --curdir
	rm -rf tmp
	mkdir tmp
	(cd tmp &&  unzip ../evanescent-0.zip)
	
install: all
	docker tag ubuntu1804-vrtogether-evanescent jackjansen/ubuntu1804-vrtogether-evanescent
	docker push jackjansen/ubuntu1804-vrtogether-evanescent:latest
 
