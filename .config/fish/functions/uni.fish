function uni --description "Go to this semester's university folder"
    for d in ~/Insync/*/"Google Drive"/University/2026/spring    # finds it without naming the account
        test -d $d; and cd $d; and return
    end
    echo "uni: this semester's folder isn't in ~/Insync" >&2
    return 1
end
