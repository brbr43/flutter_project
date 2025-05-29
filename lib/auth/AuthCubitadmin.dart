import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class Authcubitadmin extends Cubit<AuthState> {
  final Dio _dio;

  Authcubitadmin(this._dio) : super(AuthInitial());

  // دالة التسجيل
  Future<void> register(String email, String password) async {
    emit(AuthLoading());

    // التحقق من البيانات قبل إرسالها
    if (email.isEmpty || password.isEmpty) {
      emit(AuthError(message: 'الرجاء ملء جميع الحقول'));
      return;
    }

    try {
      final response = await _dio.post(
        'http://10.0.2.2:8000/api/admin/register', // API URL
        data: {
          'email': email, // البريد الإلكتروني
          'password': password, // كلمة المرور
        },
      );

      // التحقق من حالة الاستجابة
      if (response.statusCode == 201) {
        emit(AuthSuccess(message: 'تم التسجيل بنجاح'));
      } else {
        emit(AuthError(
            message:
                'حدث خطأ أثناء التسجيل: ${response.data['message'] ?? 'يرجى المحاولة لاحقًا'}'));
      }
    } catch (e) {
      print("Error during registration: $e");
      emit(AuthError(message: 'خطأ أثناء الاتصال بالخادم: $e'));
    }
  }

  Future<void> login(String email, String password) async {
    emit(AuthLoading());

    try {
      final response = await _dio.post(
        'http://10.0.2.2:8000/api/admin/login', // أو تحقق من API admin/login إذا كان الإداريين فقط
        data: {
          'email': email,
          'password': password,
        },
      );

      if (response.statusCode == 200) {
        final token = response.data['token'];

        if (token != null && token.isNotEmpty) {
          SharedPreferences prefs = await SharedPreferences.getInstance();
          await prefs.setString('token', token);
          String? storedToken = prefs.getString('token');
          print('Stored token: $storedToken');

          emit(AuthSuccess(message: 'تم تسجيل الدخول بنجاح'));
        } else {
          emit(AuthError(message: 'التوكن غير موجود في الاستجابة'));
        }
      } else {
        emit(AuthError(
            message: response.data['message'] ?? 'حدث خطأ أثناء تسجيل الدخول'));
      }
    } catch (e) {
      emit(AuthError(message: 'خطأ أثناء الاتصال بالخادم: $e'));
    }
  }

  Future<String?> getStoredToken() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }
}

abstract class AuthState {}

class AuthInitial extends AuthState {}

class AuthLoading extends AuthState {}

class AuthSuccess extends AuthState {
  final String message;
  AuthSuccess({required this.message});
}

class AuthError extends AuthState {
  final String message;
  AuthError({required this.message});
}
