#!/bin/bash

set -e

REPO_URL="${REPO_URL:-https://github.com/inpanel/repo.inpanel.org.git}"
LOCAL_DIR="${LOCAL_DIR:-../repo.inpanel.org}"

OK='\033[1;32mOK\033[0m'
FAILED='\033[1;31mFAILED\033[0m'
INFO='\033[1;34mINFO\033[0m'

info() {
    echo -e "[$INFO] $1"
}

success() {
    echo -e "[$OK] $1"
}

fail() {
    echo -e "[$FAILED] $1"
    exit 1
}

check_dependencies() {
    info "Checking dependencies..."
    
    if ! command -v git &>/dev/null; then
        fail "git is required"
    fi
    
    success "Dependencies check passed"
}

create_local_dir() {
    info "Creating local directory..."
    
    mkdir -p "$LOCAL_DIR"
    
    success "Local directory created: $LOCAL_DIR"
}

initialize_git() {
    info "Initializing git repository..."
    
    cd "$LOCAL_DIR"
    
    if [ ! -d .git ]; then
        git init
        git config user.name "Jackson Dou"
        git config user.email "jksdou@qq.com"
    fi
    
    if ! git branch -a | grep -q gh-pages; then
        git checkout --orphan gh-pages
        echo "# InPanel Repository" > README.md
        git add README.md
        git commit -m "Initial commit"
    else
        git checkout gh-pages
    fi
    
    success "Git repository initialized with gh-pages branch"
}

create_directory_structure() {
    info "Creating repository directory structure..."
    
    mkdir -p rpm/centos/7
    mkdir -p rpm/centos/8
    mkdir -p rpm/centos/9
    mkdir -p rpm/fedora
    mkdir -p deb/conf
    mkdir -p deb/dists
    mkdir -p deb/pool/main/i
    mkdir -p gpg
    
    touch rpm/centos/7/.gitkeep
    touch rpm/centos/8/.gitkeep
    touch rpm/centos/9/.gitkeep
    touch rpm/fedora/.gitkeep
    touch deb/dists/.gitkeep
    touch deb/pool/main/i/.gitkeep
    touch gpg/.gitkeep
    
    cat > deb/conf/distributions << 'EOF'
Origin: InPanel
Label: InPanel
Suite: stable
Codename: focal
Version: 1.0
Architectures: all source
Components: main
Description: InPanel Debian/Ubuntu Repository
EOF
    
    cat > deb/conf/options << 'EOF'
verbose
basedir .
EOF
    
    git add -A
    git commit -m "Add directory structure" || true
    
    success "Directory structure created"
}

add_remote() {
    info "Adding remote repository..."
    
    if ! git remote | grep -q origin; then
        git remote add origin "$REPO_URL"
    else
        git remote set-url origin "$REPO_URL"
    fi
    
    success "Remote repository configured: $REPO_URL"
}

push_to_github() {
    info "Pushing to GitHub..."
    
    git push -u origin gh-pages
    
    success "Pushed to GitHub"
}

show_next_steps() {
    echo ""
    echo "============================================="
    echo "          Repository Initialized"
    echo "============================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Enable GitHub Pages in repo.inpanel.org:"
    echo "   - Go to https://github.com/inpanel/repo.inpanel.org/settings/pages"
    echo "   - Select 'gh-pages' branch as Source"
    echo "   - Save (may take a few minutes to deploy)"
    echo ""
    echo "2. Generate GPG key (optional but recommended):"
    echo "   gpg --gen-key"
    echo "   gpg --armor --export <KEY_ID> > gpg/inpanel.gpg.key"
    echo "   git add -A && git commit -m 'Add GPG key' && git push"
    echo ""
    echo "3. Create REPO_DEPLOY_TOKEN in main repository:"
    echo "   - Go to https://github.com/settings/tokens"
    echo "   - Generate token with 'repo' scope"
    echo "   - Add to https://github.com/inpanel/inpanel/settings/secrets/actions"
    echo "   - Name: REPO_DEPLOY_TOKEN"
    echo ""
    echo "4. Configure other secrets in main repository:"
    echo "   - GPG_PRIVATE_KEY (base64 encoded): gpg --export-secret-keys <KEY_ID> | base64"
    echo "   - GPG_KEY_ID: Your GPG key ID"
    echo ""
    echo "5. Test the workflow:"
    echo "   git tag v1.2.28"
    echo "   git push origin v1.2.28"
    echo ""
    echo "Repository URL: https://inpanel.github.io/repo.inpanel.org/"
    echo ""
}

main() {
    check_dependencies
    create_local_dir
    initialize_git
    create_directory_structure
    add_remote
    push_to_github
    show_next_steps
}

main "$@"