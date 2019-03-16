# -*- coding: utf-8 -*-

import os
from uuid import uuid4

from flask import (Blueprint, Markup, current_app, flash, redirect,
                   render_template, render_template_string, request, send_file,
                   url_for)
from flask_babel import _
from flask_login import fresh_login_required, login_required

from MMCs.decorators import root_required
from MMCs.extensions import db
from MMCs.forms import (AboutEditForm, AboutImageUploadForm,
                        ChangeUsernameForm, CompetitionNameForm,
                        CompetitionSettingForm, DownloadLogForm,
                        EditProfileForm, ErrorImageUploadForm,
                        IndexImageUploadForm, NoticeEditForm, RegisterForm,
                        RootChangePasswordForm)
from MMCs.models import Competition, User
from MMCs.settings import basedir
from MMCs.utils import (download_solution_score, download_teacher_result,
                        flash_errors, redirect_back, zip2here)

root_bp = Blueprint('root', __name__)


@root_bp.route('/')
@root_required
@login_required
def index():
    return redirect(url_for('.manage_competition'))


@root_bp.route('/competition')
@root_required
@login_required
def manage_competition():
    return redirect(url_for('root.behavior'))


@root_bp.route('/competition/behavior')
@root_required
@login_required
def behavior():
    form = CompetitionNameForm()
    return render_template(
        'backstage/root/manage_competition/behavior.html', form=form)


@root_bp.route('/competition/history')
@root_required
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    pagination = Competition.query.order_by(
        Competition.id.desc()).paginate(page, current_app.config['COMPETITION_PER_PAGE'])

    return render_template(
        'backstage/root/manage_competition/history.html',
        pagination=pagination, page=page)


@root_bp.route('/competition/notice', methods=['GET', 'POST'])
@fresh_login_required
@root_required
@login_required
def notice():
    form = NoticeEditForm()
    path = os.path.join(
        basedir, current_app.name, current_app.template_folder, 'showing/notice.html')
    if form.validate_on_submit():
        with open(path, 'w', encoding='utf-8') as f:
            f.write(Markup(form.notice.data))

        flash(_('Setting updated.'), 'success')
        return redirect_back()

    with open(path, 'r', encoding='utf-8') as f:
        form.notice.data = render_template_string(f.read())

    return render_template(
        'backstage/root/manage_competition/notice.html', form=form)


@root_bp.route('/competition/settings', methods=['GET', 'POST'])
@fresh_login_required
@root_required
@login_required
def competition_settings():
    form = CompetitionSettingForm()
    if form.validate_on_submit():
        current_app.config['SOLUTION_TASK_NUMBER'] = form.solution_task_number.data
        current_app.config['USER_PER_PAGE'] = form.user_per_page.data
        current_app.config['SOLUTION_PER_PAGE'] = form.solution_per_page.data
        current_app.config['COMPETITION_PER_PAGE'] = form.competition_per_page.data
        current_app.config['DROPZONE_MAX_FILES'] = form.dropzone_max_files.data

    form.solution_task_number.data = current_app.config['SOLUTION_TASK_NUMBER']
    form.user_per_page.data = current_app.config['USER_PER_PAGE']
    form.solution_per_page.data = current_app.config['SOLUTION_PER_PAGE']
    form.competition_per_page.data = current_app.config['COMPETITION_PER_PAGE']
    form.dropzone_max_files.data = current_app.config['DROPZONE_MAX_FILES']

    return render_template(
        'backstage/root/manage_competition/notice.html', form=form)


@root_bp.route('/competition/behavior/start', methods=['POST'])
@fresh_login_required
@root_required
@login_required
def start_competition():
    form = CompetitionNameForm()
    if form.validate_on_submit():
        com = Competition(name=form.name.data, flag=True)
        db.session.add(com)
        db.session.commit()
        flash(_('A new competition start now.'), 'success')

    flash_errors(form)

    return redirect_back()


@root_bp.route('/competition/behavior/switch', methods=['POST'])
@fresh_login_required
@root_required
@login_required
def switch_state():
    com = Competition.current_competition()
    if com:
        if com.is_start():
            com.flag = False
            flash(_('Competition stopped.'), 'success')
        else:
            com.flag = True
            flash(_('Competition continued.'), 'success')
        db.session.commit()
    else:
        flash(_('Please start new competition before do it.'), 'warning')

    return redirect_back()


@root_bp.route('/personnel')
@root_required
@login_required
def manage_personnel():
    return redirect(url_for('.personnel_list'))


@root_bp.route('/personnel/list')
@root_required
@login_required
def personnel_list():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(
        User.id.desc()).paginate(page, current_app.config['USER_PER_PAGE'])

    return render_template(
        'backstage/root/manage_personnel/personnel_list.html',
        pagination=pagination, page=page)


@root_bp.route('/personnel/list/change-password/<int:user_id>', methods=['GET', 'POST'])
@fresh_login_required
@root_required
@login_required
def change_password(user_id):
    form = RootChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.get_or_404(user_id)
        user.set_password(form.password.data)
        db.session.commit()

        flash(_('Password updated.'), 'success')
        return redirect(url_for('.personnel_list'))

    return render_template(
        'backstage/root/manage_personnel/personnel_edit.html', form=form)


@root_bp.route('/personnel/list/edit-profile/<int:user_id>', methods=['GET', 'POST'])
@fresh_login_required
@root_required
@login_required
def edit_profile(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileForm()
    if form.validate_on_submit():
        user.realname = form.realname.data
        user.remark = form.remark.data
        db.session.commit()

        flash(_('Profile updated.'), 'success')
        return redirect(url_for('.personnel_list'))

    form.realname.data = user.realname
    form.remark.data = user.remark

    return render_template(
        'backstage/root/manage_personnel/personnel_edit.html', form=form)


@root_bp.route('/personnel/list/change-username/<int:user_id>', methods=['GET', 'POST'])
@fresh_login_required
@root_required
@login_required
def change_username(user_id):
    user = User.query.get_or_404(user_id)
    form = ChangeUsernameForm()
    if form.validate_on_submit():
        user.username = form.username.data
        db.session.commit()

        flash(_('Username updated.'), 'success')
        return redirect(url_for('.personnel_list'))

    form.username.data = user.username
    form.username2.data = user.username

    return render_template(
        'backstage/root/manage_personnel/personnel_edit.html', form=form)


@root_bp.route('/personnel/register', methods=['GET', 'POST'])
@fresh_login_required
@root_required
@login_required
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            realname=form.realname.data,
            permission=form.permission.data,
            remark=form.remark.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Account registered.'), 'success')
        return redirect_back()

    return render_template('backstage/root/manage_personnel/register.html', form=form)


@root_bp.route('/delete/user/<int:user_id>', methods=['POST'])
@fresh_login_required
@root_required
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    flash(_('User deleted.'), 'info')

    return redirect_back()


@root_bp.route('/score/download/<int:competition_id>/teacher', methods=['POST'])
@fresh_login_required
@root_required
@login_required
def download_teacher(competition_id):
    com = Competition.query.get_or_404(competition_id)
    if com.tasks:
        zfile = download_teacher_result(competition_id)

        flash(_('The result file is already downloaded.'), 'success')
        return send_file(zfile, as_attachment=True)
    else:
        flash(_('No task.'), 'warning')
        return redirect_back()


@root_bp.route('/score/download/<int:competition_id>/result', methods=['POST'])
@fresh_login_required
@root_required
@login_required
def download_result(competition_id):
    com = Competition.query.get_or_404(competition_id)
    if com.solutions:
        zfile = download_solution_score(competition_id)

        flash(_('The result file is already downloaded.'), 'success')
        return send_file(zfile, as_attachment=True)

    else:
        flash('No solution.', 'warning')
        return redirect_back()


@root_bp.route('/settings')
@root_required
@login_required
def system_settings():
    return redirect(url_for('root.logs'))


@root_bp.route('/settings/logs')
@fresh_login_required
@root_required
@login_required
def logs():
    form = DownloadLogForm()
    return render_template(
        'backstage/root/manage_settings/logs.html', form=form)


@root_bp.route('/settings/logs/download', methods=['POST'])
@fresh_login_required
@root_required
@login_required
def logs_download():
    if os.path.exists(os.path.join(basedir, 'logs', 'MMCs.log')):
        file = os.path.join(
            current_app.config['FILE_CACHE_PATH'], uuid4().hex + '.zip')
        zip2here(os.path.join(basedir, 'logs'), file)

        return send_file(file, as_attachment=True)
    else:
        flash('No logs.', 'warning')
        return redirect_back()


@root_bp.route('/settings/about', methods=['GET', 'POST'])
@fresh_login_required
@root_required
@login_required
def about():
    form = AboutEditForm()
    path = os.path.join(
        basedir, current_app.name, current_app.template_folder, 'showing/about.html')
    if form.validate_on_submit():
        with open(path, 'w', encoding='utf-8') as f:
            f.write(Markup(form.about.data))

        flash(_('Setting updated.'), 'success')
        return redirect_back()

    with open(path, 'r', encoding='utf-8') as f:
        form.about.data = render_template_string(f.read())

    return render_template('backstage/root/manage_settings/about.html', form=form)


@root_bp.route('/settings/images', methods=['GET', 'POST'])
@fresh_login_required
@root_required
@login_required
def images():
    index_form = IndexImageUploadForm()
    about_form = AboutImageUploadForm()
    error_form = ErrorImageUploadForm()
    if request.method == 'POST':
        path = os.path.join(basedir, current_app.name, 'static', 'images')
        img = request.files.get('file')
        if index_form.index_upload.data and index_form.validate_on_submit():
            img.save(os.path.join(path, 'index.jpg'))
            flash(_('Image updated.'), 'success')

        if about_form.about_upload.data and about_form.validate_on_submit():
            img.save(os.path.join(path, 'about.jpg'))
            flash(_('Image updated.'), 'success')

        if error_form.error_upload.data and error_form.validate_on_submit():
            img.save(os.path.join(path, 'error.jpg'))
            flash(_('Image updated.'), 'success')

        flash_errors(index_form)
        flash_errors(about_form)
        flash_errors(error_form)

        return redirect_back()

    return render_template(
        'backstage/root/manage_settings/images.html',
        index_form=index_form, about_form=about_form, error_form=error_form)
