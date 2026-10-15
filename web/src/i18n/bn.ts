/** bn.ts — All user-facing Bangla strings (FRONT-3) */
const bn = {
  appName:         'চাষের দিশা',
  appTagline:      'কৃষকের বিশ্বস্ত সহায়ক',

  // Auth
  username:        'ব্যবহারকারীর নাম',
  password:        'পাসওয়ার্ড',
  login:           'প্রবেশ করুন',
  logout:          'প্রস্থান',
  loginFailed:     'লগইন ব্যর্থ। ব্যবহারকারীর নাম ও পাসওয়ার্ড পরীক্ষা করুন।',

  // Chat
  chatPlaceholder: 'এখানে লিখুন…',
  send:            'পাঠান',
  thinking:        'ভাবছি…',
  chatError:       'উত্তর দিতে সমস্যা হচ্ছে। আবার চেষ্টা করুন।',
  youLabel:        'আপনি',
  botLabel:        'চাষের দিশা',
  emptyChat:       'কৃষি বিষয়ক যেকোনো প্রশ্ন করুন।',

  // Side-menu (FRONT-4)
  newChat:         'নতুন চ্যাট',
  clearChat:       'চ্যাট মুছুন',
  exportChat:      'চ্যাট ডাউনলোড',
  endSession:      'সেশন শেষ করুন',

  // Weather
  weatherTitle:    'আবহাওয়া',
  weatherBtn:      'আবহাওয়া দেখুন',
  locating:        'অবস্থান খুঁজছি…',
  locationError:   'অবস্থান পাওয়া যায়নি। GPS চালু আছে কিনা দেখুন।',
  weatherError:    'আবহাওয়া তথ্য পাওয়া যায়নি।',
  temp:            'তাপমাত্রা',
  humidity:        'আর্দ্রতা',
  rain:            'বৃষ্টির সম্ভাবনা',
  wind:            'বাতাসের গতি',
  uv:              'UV সূচক',
  rain3d:          '৩ দিনের বৃষ্টি',
  et0:             'ET₀ (সেচ)',
  agriAdvice:      'কৃষি পরামর্শ',

  // Disease detection (FRONT-5)
  diseaseTitle:    'রোগ শনাক্তকরণ',
  uploadImage:     'ধানের পাতার ছবি আপলোড করুন',
  analyzing:       'বিশ্লেষণ করছি…',
  diseaseResult:   'শনাক্ত রোগ',
  confidence:      'নির্ভরযোগ্যতা',
  advice:          'পরামর্শ',
  healthy:         'সুস্থ গাছ',
  modelNotReady:   'মডেল এখনও প্রস্তুত নয়। প্রশিক্ষণ শেষ হলে পুনরায় চেষ্টা করুন।',

  // Fertilizer (FRONT-6)
  fertilizerTitle: 'সার পরামর্শ',
  crop:            'ফসল',
  soilType:        'মাটির ধরন',
  growthStage:     'বৃদ্ধির পর্যায়',
  symptoms:        'সমস্যার লক্ষণ',
  getFertAdvice:   'পরামর্শ নিন',
  fertResult:      'সার পরামর্শ',

  // Generic
  loading:         'লোড হচ্ছে…',
  error:           'ত্রুটি',
  retry:           'আবার চেষ্টা করুন',
  close:           'বন্ধ করুন',
  darkMode:        'রাত মোড',
  lightMode:       'দিন মোড',
};

export default bn;
