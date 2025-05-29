import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthCubit extends Cubit<AuthState> {
  final Dio _dio;

  AuthCubit(this._dio) : super(AuthInitial());

  // دالة التسجيل
  Future<void> register(String phone, String email, int apartmentNumber,
      String complexName, String password) async {
    emit(AuthLoading());

    // التحقق من البيانات قبل إرسالها
    if (phone.isEmpty ||
        email.isEmpty ||
        apartmentNumber == null ||
        complexName.isEmpty ||
        password.isEmpty) {
      emit(AuthError(message: 'الرجاء ملء جميع الحقول'));
      return;
    }

    try {
      // إعداد Dio لتجاهل الإعادة التوجيه
      _dio.options.followRedirects =
          true; // أو False إذا كنت لا تريد اتباع إعادة التوجيه
      final response = await _dio.post(
        'http://10.0.2.2:8000/api/register', // API URL
        data: {
          'phone_number': phone, // رقم الهاتف
          'email': email, // البريد الإلكتروني
          'apartment_number': apartmentNumber, // رقم الشقة
          'complex_name': complexName, // اسم المجمع السكني
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
      // إظهار رسالة الخطأ التفصيلية في حالة حدوث خطأ
      print("Error during registration: $e");
      emit(AuthError(message: 'خطأ أثناء الاتصال بالخادم: $e'));
    }
  }

  Future<void> login(String email, String password) async {
    emit(AuthLoading());

    try {
      final response = await _dio.post(
        'http://10.0.2.2:8000/api/login',
        data: {
          'email': email,
          'password': password,
        },
      );

      if (response.statusCode == 200) {
        // Get the token from the correct key
        final token = response.data['access_token'];

        // Check if the token exists before storing it
        if (token != null) {
          SharedPreferences prefs = await SharedPreferences.getInstance();
          await prefs.setString('auth_token', token);
          String? storedToken = prefs.getString('auth_token');
          print('Stored token: $storedToken');

          emit(AuthSuccess(message: 'Login successful.'));
        } else {
          emit(AuthError(message: 'Token not found in the response.'));
        }
      } else {
        emit(AuthError(message: 'An error occurred during login.'));
      }
    } catch (e) {
      emit(AuthError(message: 'The email or password is incorrect'));
    }
  }

  // دالة استرجاع التوكن المخزن
  Future<String?> getStoredToken() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
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
