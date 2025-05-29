import 'package:campoundnew/model/User.dart';
import 'package:dio/dio.dart';

class UsersApi {
  final Dio _dio = Dio();

  // قم بإنشاء دالة لجلب بيانات المستخدمين
  Future<List<User>> getUsers() async {
    try {
      final response = await _dio.get('http://10.0.2.2:8000/api/users');

      if (response.statusCode == 200) {
        // تحويل البيانات إلى قائمة من الكائنات User
        List<dynamic> data = response.data;
        return data.map((user) => User.fromJson(user)).toList();
      } else {
        throw Exception('فشل في تحميل البيانات');
      }
    } catch (e) {
      throw Exception('خطأ أثناء الاتصال بالخادم: $e');
    }
  }

  // دالة لتحديث بيانات مستخدم
  Future<void> updateUser(String userId, String email, String phone,
      String apartment, String complex) async {
    try {
      // إرسال الطلب إلى API لتحديث البيانات بناءً على ID المستخدم
      final response = await _dio.put(
        'http://10.0.2.2:8000/api/users/$userId',
        data: {
          'email': email,
          'phone_number': phone,
          'apartment_number': apartment,
          'complex_name': complex,
        },
      );

      if (response.statusCode == 200) {
        print('تم تحديث البيانات بنجاح');
      } else {
        throw Exception('فشل في تحديث البيانات');
      }
    } catch (e) {
      throw Exception('فشل في تحديث البيانات: $e');
    }
  }

  // حذف مستخدم
  Future<void> deleteUser(String userId) async {
    try {
      await _dio.delete('http://10.0.2.2:8000/api/users/$userId');
    } catch (e) {
      throw Exception('Failed to delete user: $e');
    }
  }
}
