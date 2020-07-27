from flask_tools import (
    GetApp,
    GetUser,
    VerifyLogin,
    SetupRegisterAndLoginPageWithPassword,
)
from flask import redirect, render_template

app = GetApp(
    'Login App',
)
SetupRegisterAndLoginPageWithPassword(
    app,
    mainTemplate='base.html',
    redirectSuccess='/'
)


@app.route('/')
@VerifyLogin
def Index():
    return "you are logged in <a href='/logout'>Logout</a>"


if __name__ == '__main__':
    app.run(debug=True)
