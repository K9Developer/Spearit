from spear_head.constants import SPEAR_HEAD_WRAPPER_PORT
from spear_head.models.connection.socket_server import SocketServer
from spear_head.spear_head import SpearHead

def main():
    sh = SpearHead()
    sh.start()


if __name__ == "__main__":
    main()