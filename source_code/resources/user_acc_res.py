from flask import Response, request
from source_code.resources.main_res import MainRes


class UserAccRes(MainRes):
    # Вход в аккаунт с помощью логина и пароля
    def post(self):
        login: str = request.form.get('login')
        password: str = request.form.get('password')
        json_model = self.api_connector.loginByPassword(login, password)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="LoginByPassword", event_json={
                "login": login,
                "password": password,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(status=401)

    # Вход в аккаунт с помощью хэша
    def put(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        json_model = self.api_connector.loginByHash(hash_user)
        if json_model:
            self.app_metrica_reporter.sendEvent(event_name="LoginByHash", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
            })
            return Response(json_model, mimetype='application/json')
        else:
            return Response(status=401)

    # Выход из аккаунта с помощью хэша
    def delete(self):
        hash_user: str = request.form.get('hash')
        acc_id, error_response = self.check_user_access(hash_user)
        if error_response:
            return error_response

        checker = self.api_connector.logoutByHash(hash_user)
        if checker:
            self.app_metrica_reporter.sendEvent(event_name="LogoutByHash", event_json={
                "hash": hash_user,
                "acc_id": acc_id,
            })
            return Response(status=200)
        else:
            return Response(status=401)
