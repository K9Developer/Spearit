#define MAX_LSM_LINKS 32
#include <bpf/libbpf.h>
#include <stdlib.h>

static struct bpf_link *lsm_links[MAX_LSM_LINKS];
static int lsm_links_count = 0;

int attach_lsm(struct bpf_object *obj)
{
    struct bpf_program *prog;
    int lsm_attached = 0;

    bpf_object__for_each_program(prog, obj) {
        const char *section = bpf_program__section_name(prog);
        const char *name    = bpf_program__name(prog);

        if (!section || strncmp(section, "lsm/", 4) != 0)
            continue;

        if (lsm_links_count >= MAX_LSM_LINKS) {
            fprintf(stderr, "Too many LSM programs, increase MAX_LSM_LINKS\n");
            return -1;
        }

        struct bpf_link *link = bpf_program__attach(prog);
        if (libbpf_get_error(link)) {
            fprintf(stderr, "Failed to attach LSM program: %s (%s)\n", name ? name : "<noname>", section);
            return -1;
        }

        lsm_links[lsm_links_count++] = link;
        printf("Attached LSM prog: %s (%s)\n", name ? name : "<noname>", section);

        lsm_attached = 1;
    }

    if (!lsm_attached) {
        fprintf(stderr, "No LSM programs found in object\n");
        return -1;
    }

    printf("LSM programs loaded and attached.\n");
    return 0;
}

void detach_lsm(void)
{
    for (int i = 0; i < lsm_links_count; i++) {
        if (!lsm_links[i])
            continue;

        bpf_link__destroy(lsm_links[i]);
        lsm_links[i] = NULL;
    }

    lsm_links_count = 0;
    printf("LSM programs detached.\n");
}