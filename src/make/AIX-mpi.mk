CXX:=mpCC
CXXFLAGS:= -DUSE_MPI -q64 -qrtti $(INCLUDEPATH) -O3 -qstrict
DEBUG:= -DNDEBUG -DDEBUG_WRITE 
LDFLAGS:=


DEPENDMAKER:=g++ -MM  $(INCLUDEPATH)

