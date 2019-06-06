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
	mv evanescent-*.tar.bz2 tmp
	(cd tmp &&  tar xf evanescent-*.tar.bz2 && ln -s evanescent/[0-9]* installed)
	
install: all
	docker tag ubuntu1804-vrtogether-evanescent jackjansen/ubuntu1804-vrtogether-evanescent
	docker push jackjansen/ubuntu1804-vrtogether-evanescent:latest
 
