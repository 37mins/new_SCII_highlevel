/* CPU test only: pause real GNU du after discovering one directory entry.
 * This forces rename between readdir and stat without changing du's errors. */
#define _GNU_SOURCE
#include <dirent.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void pause_entry(const char *name) {
    const char *target = getenv("SC2_DU_PAUSE_NAME");
    const char *ready = getenv("SC2_DU_PAUSE_READY");
    const char *release = getenv("SC2_DU_PAUSE_RELEASE");
    if (!target || !ready || !release || strcmp(name, target)) return;
    int fd = open(ready, O_CREAT | O_WRONLY, 0600);
    if (fd < 0) _exit(120);
    close(fd);
    for (int i = 0; i < 5000; ++i) {
        if (access(release, F_OK) == 0) return;
        usleep(1000);
    }
    _exit(121);
}

struct dirent *readdir(DIR *dir) {
    struct dirent *(*next)(DIR *) = dlsym(RTLD_NEXT, "readdir");
    struct dirent *entry = next(dir);
    if (entry) pause_entry(entry->d_name);
    return entry;
}

struct dirent64 *readdir64(DIR *dir) {
    struct dirent64 *(*next)(DIR *) = dlsym(RTLD_NEXT, "readdir64");
    struct dirent64 *entry = next(dir);
    if (entry) pause_entry(entry->d_name);
    return entry;
}
