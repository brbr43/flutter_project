import 'package:campoundnew/model/ProfileModel.dart';
import 'package:dio/dio.dart';

class ApiService {
  final Dio _dio = Dio();
  final String baseUrl = "http://10.0.2.2:8000/api/profile";

  Future<ProfileModel?> fetchProfile(String token) async {
    try {
      if (token.isEmpty) {
        print("❌ خطأ: التوكن غير متوفر!");
        return null;
      }

      print("✅ التوكن المستخدم: $token");

      Response response = await _dio.get(
        baseUrl,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Accept': 'application/json',
          },
        ),
      );

      print("📥 استجابة الـ API: ${response.data}");

      if (response.statusCode == 200) {
        return ProfileModel.fromJson(response.data['user']);
      } else {
        print("❌ فشل في تحميل البيانات، كود الحالة: ${response.statusCode}");
        return null;
      }
    } catch (e) {
      print("❌ خطأ أثناء تحميل البيانات: $e");
      return null;
    }
  }
}
