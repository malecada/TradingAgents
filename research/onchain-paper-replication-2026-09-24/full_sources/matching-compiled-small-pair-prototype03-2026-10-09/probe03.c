#include <stdio.h>
#include <linux/fcntl.h>
#include <linux/memfd.h>
int main(void) {
 printf("{\"F_ADD_SEALS\":%d,\"F_GET_SEALS\":%d,\"F_SEAL_WRITE\":%d,\"F_SEAL_GROW\":%d,\"F_SEAL_SHRINK\":%d,\"F_SEAL_SEAL\":%d,\"MFD_CLOEXEC\":%u,\"MFD_ALLOW_SEALING\":%u}\n",F_ADD_SEALS,F_GET_SEALS,F_SEAL_WRITE,F_SEAL_GROW,F_SEAL_SHRINK,F_SEAL_SEAL,MFD_CLOEXEC,MFD_ALLOW_SEALING);
 return 0;
}
