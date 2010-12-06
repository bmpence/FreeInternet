import os
import socket
import logging

_ROOT_DIRECTORY = "/home/ben/Source/FreeInternet/"
_DEFAULT_PATH = "classes/serverFiles/"

_DEFAULT_HOST = 'localhost'
_DEFAULT_PORT = 5555
_CHUNK_SIZE = 4096

_JOIN_CHARACTER = "|"
_PAD_CHARACTER = "."

_WAIT_FOR_SEND = "send"
_WAIT_FOR_RECV = "recv"

class Protocol(object):
    def __init__(self, caller, sock, direction, address):
        self.caller = caller
        self.sock = sock
        self.direction = direction
        self.address = address

    def __str__(self):
        return self.address

    def pad(cls, l):
        if type(l) is list:
            string = _JOIN_CHARACTER.join(l) + _JOIN_CHARACTER
        else:
            string = l + _JOIN_CHARACTER

        while len(string) < _CHUNK_SIZE:
            string += _PAD_CHARACTER
        return string

    def unpad(self, t):
        l = t.split(_JOIN_CHARACTER)[:-1]
        
        if len(l) == 1:
            return l[0]
        else:
            return l

    def writeFile(self, file, data):
        try:
            file.write(data)
        except IOError:
            logging.Logger.log(str(self.caller),
                               "[%s] "
                               "Error writing to file %s" % (str(self), file.name),
                               messageType="ERR")

    def readFile(self, file, amount=_CHUNK_SIZE):
        try:
            data = file.read(amount)
        except IOError:
            logging.Logger.log(str(self.caller),
                               "[%s] "
                               "Error reading from file %s" % (str(self), file.name),
                               messageType="ERR")
            return None
        return data


    def sendData(self, data, binary=None):
        try:
            if binary:
                self.sock.send(data)
            else:
                self.sock.send(self.pad(data))
        except socket.error, e:
            logging.Logger.log(str(self.caller),
                               "[%s] "
                               "Error sending" % str(self),
                               messageType = "ERR")
            return None
        return True

    def recvData(self, binary=None):
        try:
            if binary:
                data = self.sock.recv(binary)
            else:
                data = self.unpad(self.sock.recv(_CHUNK_SIZE))
        except socket.error, e:
            logging.Logger.log(str(self.caller),
                               "[%s] "
                               "Error receiving" % str(self),
                               messageType = "ERR")
            return None
        return data

    def actions(self):
        pass
                    
    def dummyActions(self):
        pass

class ProtocolEcho(Protocol):
    _FROM_CLIENT = "fromClient"
    _FROM_SERVER = "fromServer"

    def __init__(self, caller, sock, direction, address):
        super(ProtocolEcho, self).__init__(caller, sock, direction, address)

    def actions(self):
        # Client -> Server
        if self.direction == self._FROM_CLIENT:
            # Server
            if str(self.caller).startswith("server"):
                return self.recv()

            # Client
            else:
                return self.send()
                
        # Server -> Client
        elif self.direction == self._FROM_SERVER:
            # Server
            if str(self.caller).startswith("server"):
                return self.send()

            # Client
            else:
                return self.recv()

        else:
            logging.Logger.log(str(self.caller),
                               "[%s] "
                               "BAD DIRECTION" % str(self),
                               messageType = "ERR")
            return self.dummyActions()

    def send(self):
        yield _WAIT_FOR_SEND
        self.sendData("GOOD MORNING")

        yield _WAIT_FOR_RECV
        data = self.recvData()
        print data

        yield _WAIT_FOR_SEND
        self.sendData("HOW ARE YOU?")

        yield _WAIT_FOR_RECV
        data = self.recvData()
        print data

        yield _WAIT_FOR_SEND
        self.sendData("TA")

        yield _WAIT_FOR_RECV
        data = self.recvData()
        print data

    def recv(self):
        yield _WAIT_FOR_RECV
        data = self.recvData()
        print data

        yield _WAIT_FOR_SEND
        self.sendData("GOOD MORNING")

        yield _WAIT_FOR_RECV
        data = self.recvData()
        print data

        yield _WAIT_FOR_SEND
        self.sendData("GOOD, GOOD.")

        yield _WAIT_FOR_RECV
        data = self.recvData()
        print data

        yield _WAIT_FOR_SEND
        self.sendData("TA")

class ProtocolFile(Protocol):
    _JOB_NEW = "new"
    _JOB_OLD = "old"

    def __init__(self, caller, sock, direction, address, directory=_DEFAULT_PATH, jobID=None):
        super(ProtocolFile, self).__init__(caller, sock, direction, address)

        self.directory = os.path.join(_ROOT_DIRECTORY, directory)

        if jobID:
            self.jobID = jobID

    def actions(self):
        # Server -> Client
        if self.direction == self._JOB_NEW:
            # Server
            if str(self.caller).startswith("server"):
                return self.send(ProtocolFile.getJobID())

            # Client
            else:
                return self.recv()
                
        # Client -> Server
        elif self.direction == self._JOB_OLD:
            # Server
            if str(self.caller).startswith("server"):
                return self.recv()

            # Client
            else:
                return self.send(self.jobID)

        else:
            logging.Logger.log(str(self.caller),
                               "[%s] "
                               "BAD DIRECTION" % str(self),
                               messageType = "ERR")
            return self.dummyActions()

    @classmethod
    def getJobID(cls):
        return 123

    def send(self, jobID):
        # Send jobID
        yield _WAIT_FOR_SEND
        self.sendData(str(jobID))

        # Send filesize
        yield _WAIT_FOR_SEND
        filepath = os.path.join(self.directory, str(jobID))
        filesize = bytesLeft = os.path.getsize(filepath)
        self.sendData(str(filesize))

        # Send file binary data
        file = open(filepath, 'rb')

        while bytesLeft > 0:
            yield _WAIT_FOR_SEND
            if bytesLeft < _CHUNK_SIZE:
                self.sendData(self.readFile(amount=bytesLeft), binary=True)
            else:
                self.sendData(self.readFile(file), binary=True)
            bytesLeft -= _CHUNK_SIZE

        file.close()

    def recv(self):
        # Receive jobID
        yield _WAIT_FOR_RECV
        jobID = self.recvData()

        # Receive filesize
        yield _WAIT_FOR_RECV
        filesize = bytesLeft = int(self.recvData())

        # Receive file binary data
        filepath = os.path.join(self.directory, jobID)
        file = open(filepath, 'wb')

        while bytesLeft > 0:
            yield _WAIT_FOR_RECV
            if bytesLeft < _CHUNK_SIZE:
                self.writeFile(file, self.recvData(binary=bytesLeft))
            else:
                self.writeFile(file, self.recvData(binary=_CHUNK_SIZE))
            bytesLeft -= _CHUNK_SIZE

        file.close()

class ProtocolMessage(ProtocolEcho):
    _FROM_CLIENT = "fromClient"
    _FROM_SERVER = "fromServer"

    _END_OF_STREAM = '\\'

    def __init__(self, caller, sock, direction, address, messages=[]):
        super(ProtocolMessage, self).__init__(caller, sock, direction, address)
        self.messages = messages

    def send(self):
        for message in self.messages:
            self.sendData(message)
            yield _WAIT_FOR_SEND
        
        yield _WAIT_FOR_SEND
        self.sendData(self._END_OF_STREAM)

    def recv(self):

        yield _WAIT_FOR_RECV
        data = self.recvData()

        while data != self._END_OF_STREAM:
            print data
            yield _WAIT_FOR_RECV
            data = self.recvData()

class ProtocolFile(Protocol):
    _JOB_NEW = "new"
    _JOB_OLD = "old"

    def __init__(self, caller, sock, direction, address, directory=_DEFAULT_PATH, jobID=None):
        super(ProtocolFile, self).__init__(caller, sock, direction, address)

        self.directory = os.path.join(_ROOT_DIRECTORY, directory)

        if jobID:
            self.jobID = jobID

    def actions(self):
        # Server -> Client
        if self.direction == self._JOB_NEW:
            # Server
            if str(self.caller).startswith("server"):
                return self.send(ProtocolFile.getJobID())

            # Client
            else:
                return self.recv()
                
        # Client -> Server
        elif self.direction == self._JOB_OLD:
            # Server
            if str(self.caller).startswith("server"):
                return self.recv()

            # Client
            else:
                return self.send(self.jobID)

        else:
            logging.Logger.log(str(self.caller),
                               "[%s] "
                               "BAD DIRECTION" % str(self),
                               messageType = "ERR")
            return self.dummyActions()

    @classmethod
    def getJobID(cls):
        return 123

    def send(self, jobID):
        # Send jobID
        yield _WAIT_FOR_SEND
        self.sendData(str(jobID))

        # Send filesize
        yield _WAIT_FOR_SEND
        filepath = os.path.join(self.directory, str(jobID))
        filesize = bytesLeft = os.path.getsize(filepath)
        self.sendData(str(filesize))

        # Send file binary data
        file = open(filepath, 'rb')

        while bytesLeft > 0:
            yield _WAIT_FOR_SEND
            if bytesLeft < _CHUNK_SIZE:
                self.sendData(self.readFile(file, amount=bytesLeft), binary=True)
            else:
                self.sendData(self.readFile(file), binary=True)
            bytesLeft -= _CHUNK_SIZE

        file.close()

    def recv(self):
        # Receive jobID
        yield _WAIT_FOR_RECV
        jobID = self.recvData()

        # Receive filesize
        yield _WAIT_FOR_RECV
        filesize = bytesLeft = int(self.recvData())

        # Receive file binary data
        filepath = os.path.join(self.directory, jobID)
        file = open(filepath, 'wb')

        while bytesLeft > 0:
            yield _WAIT_FOR_RECV
            if bytesLeft < _CHUNK_SIZE:
                self.writeFile(file, self.recvData(binary=bytesLeft))
            else:
                self.writeFile(file, self.recvData(binary=_CHUNK_SIZE))
            bytesLeft -= _CHUNK_SIZE

        file.close()


_PROTOCOLS = {"file"    : ProtocolFile,
              "echo"    : ProtocolEcho,
              "message" : ProtocolMessage}
