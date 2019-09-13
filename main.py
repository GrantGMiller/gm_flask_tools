@app.route('/add_content', methods=['GET', 'POST'])
@VerifyLogin
def AddContent():
    print('AddContent()')
    form = ContentForm()

    if form.validate_on_submit():
        print('validated')

        extension = form.file.data.filename.split('.')[-1].lower()
        url = '/static/user_content/{}.{}'.format(GetRandomID(), extension)

        form.file.data.save(url[1:])

        size = os.stat(url[1:]).st_size  # in bytes
        sizeString = '{:,} Bytes'.format(size)

        if extension in ['jpg', 'png', 'gif']:
            thumbnailURL = MakeThumbnail(url[1:])

        elif extension in ['mp4', 'flv']:
            thumbnailURL = MakeVideoThumbnail(url[1:])
            if thumbnailURL is None:
                thumbnailURL = 'static/user_content/thumbnail.jpg'

        else:
            thumbnailURL = MakeThumbnail(url[1:])

        print('137 thumbnailURL=', thumbnailURL)

        user = GetUser()
        maxContent = user.get('maxNumContent', 10)
        allContent = FindAll(ContentClass, owner=user.get('email'))
        if len(allContent) >= maxContent:
            flash(
                'Cannot add content. Your account has a maximum of {} content items. Please contact grant@grant-miller.com to upgrade your account.'.format(
                    maxContent,
                ))
            return redirect('/content')

        newContent = ContentClass(
            owner=GetUser().get('email'),
            name=form.name.data,
            url=url,
            size=sizeString,
            thumbnailURL=thumbnailURL,
            url_1920x1080='/' + OptimizeToSize(url[1:], maxWidth=1920, maxHeight=1080),
            url_1280x720='/' + OptimizeToSize(url[1:], maxWidth=1280, maxHeight=720),
        )
        return redirect('/content')
    else:
        print('not validated')
        for item in form.errors:
            flash(item, 'error')

        return render_template(
            'add_content.html',
            form=form,
            menuOptions=GetMenuOptions(active='Content')
        )
