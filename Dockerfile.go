FROM golang:1.25-bookworm

RUN useradd --create-home --shell /bin/bash runner

# HumanEval-X Go tests use github.com/stretchr/testify/assert.
#
# Build and test a tiny dummy module during image creation so Go resolves
# testify plus its complete transitive dependency graph while networking
# is available. The downloaded modules remain in /go/pkg/mod and can then
# be used during benchmark execution with networking completely disabled.
RUN mkdir -p /opt/migrate-eval-deps \
    && cd /opt/migrate-eval-deps \
    && printf '%s\n' \
        'module migrateevaldeps' \
        '' \
        'go 1.25' \
        '' \
        'require github.com/stretchr/testify v1.9.0' \
        > go.mod \
    && printf '%s\n' \
        'package migrateevaldeps' \
        '' \
        'import (' \
        '    "testing"' \
        '    "github.com/stretchr/testify/assert"' \
        ')' \
        '' \
        'func TestDependency(t *testing.T) {' \
        '    assert.Equal(t, 1, 1)' \
        '}' \
        > deps_test.go \
    && go mod tidy \
    && go test ./... \
    && rm -rf /opt/migrate-eval-deps

WORKDIR /work

USER runner

CMD ["go", "version"]
