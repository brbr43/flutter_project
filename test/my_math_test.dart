import 'package:flutter_test/flutter_test.dart';
import 'package:campoundnew/utils/my_math.dart';

void main() {
  test('اختبار دالة الضرب', () {
    expect(multiply(3, 4), 12);
    expect(multiply(0, 5), 0);
  });
}
