//©///////////////////////////////////////////////////////////////////////////©//
//
//  Copyright 2021-2024 BIA-Technologies Limited Liability Company
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
//
//©///////////////////////////////////////////////////////////////////////////©//

#Область СлужебныйПрограммныйИнтерфейс

Процедура ОстановитьТестКлиент() Экспорт
	Память = Мсп_СостояниеКлиент.ПолучитьСостояниеЗначение("ПамятьТестКлиент");
	
	Если Память = Неопределено Или НЕ Память.Свойство("ТестКлиент") Или ТипЗнч(Память.ТестКлиент) <> Тип("ТестируемоеПриложение") Тогда
		Результат = Мсп_УправлениеТестКлиентом.Подключиться(1999);
		Если НЕ Результат.Успех Тогда
			Возврат;
		КонецЕсли;
	КонецЕсли;
	
	Мсп_УправлениеТестКлиентом.Закрыть(, Истина);
КонецПроцедуры

#КонецОбласти
