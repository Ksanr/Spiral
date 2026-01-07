import asyncio
from typing import List
import httpx
from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    """Направления движения по спирали"""
    DOWN = (1, 0)
    RIGHT = (0, 1)
    UP = (-1, 0)
    LEFT = (0, -1)


@dataclass
class SpiralTraverser:
    """Класс для обхода матрицы по спирали против часовой стрелки"""

    @staticmethod
    def traverse(matrix: List[List[int]]) -> List[int]:
        """Обход квадратной матрицы по спирали против часовой стрелки"""
        if not matrix:
            return []

        n = len(matrix)
        result = []

        # Границы обхода
        top, bottom = 0, n - 1
        left, right = 0, n - 1

        while top <= bottom and left <= right:
            # Движение вниз по левому краю
            for i in range(top, bottom + 1):
                result.append(matrix[i][left])
            left += 1

            # Движение вправо по нижней строке
            for j in range(left, right + 1):
                result.append(matrix[bottom][j])
            bottom -= 1

            # Если еще есть строки для обхода
            if left <= right:
                # Движение вверх по правому краю
                for i in range(bottom, top - 1, -1):
                    result.append(matrix[i][right])
                right -= 1

            # Если еще есть столбцы для обхода
            if top <= bottom:
                # Движение влево по верхней строке
                for j in range(right, left - 1, -1):
                    result.append(matrix[top][j])
                top += 1

        return result


class MatrixParser:
    """Класс для парсинга матрицы из текстового представления"""

    @staticmethod
    def parse_matrix(text: str) -> List[List[int]]:
        """Парсинг матрицы из текстового представления"""
        lines = text.strip().split('\n')
        matrix = []

        for line in lines:
            line = line.strip()
            # Пропускаем строки с границами (начинаются с +)
            if line.startswith('+'):
                continue

            # Парсим строку с числами
            if '|' in line:
                # Убираем начальный и конечный '|', разделяем по '|'
                numbers = line.strip('|').split('|')
                row = []
                for num in numbers:
                    # Очищаем от пробелов и конвертируем в int
                    cleaned_num = num.strip()
                    if cleaned_num:
                        row.append(int(cleaned_num))
                if row:  # Добавляем только непустые строки
                    matrix.append(row)

        # Проверка, что матрица квадратная
        if matrix:
            n = len(matrix)
            for row in matrix:
                if len(row) != n:
                    raise ValueError(f"Матрица не квадратная: ожидалось {n}x{n}, получено {len(row)} столбцов")

        return matrix


class MatrixClient:
    """Клиент для получения и обработки матрицы с сервера"""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def fetch_matrix(self, url: str) -> List[List[int]]:
        """Загрузка и парсинг матрицы с сервера"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)

        try:
            response = await self.client.get(url)
            response.raise_for_status()  # Выбрасывает исключение для статусов 4xx/5xx

            # Парсим матрицу из ответа
            matrix = MatrixParser.parse_matrix(response.text)

            if not matrix:
                raise ValueError("Получена пустая матрица")

            return matrix

        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Ошибка сервера: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ConnectionError(f"Сетевая ошибка: {str(e)}") from e
        except ValueError as e:
            raise ValueError(f"Ошибка парсинга матрицы: {str(e)}") from e


async def get_matrix(url: str) -> List[int]:
    """
    Асинхронная функция для получения матрицы с сервера и возврата 
    результата обхода по спирали против часовой стрелки.

    Args:
        url (str): URL для загрузки матрицы

    Returns:
        List[int]: Список элементов матрицы в порядке обхода по спирали

    Raises:
        ConnectionError: При ошибках сети или сервера
        ValueError: При ошибках парсинга или некорректной матрице
    """
    async with MatrixClient() as client:
        try:
            # Получаем матрицу с сервера
            matrix = await client.fetch_matrix(url)

            # Выполняем обход по спирали
            return SpiralTraverser.traverse(matrix)

        except (ConnectionError, ValueError) as e:
            # Перебрасываем ожидаемые исключения
            raise
        except Exception as e:
            # Обрабатываем неожиданные исключения
            raise ConnectionError(f"Неожиданная ошибка: {str(e)}") from e


# Дополнительные утилиты для тестирования
async def get_matrix_safe(url: str) -> List[int]:
    """Безопасная версия get_matrix с обработкой всех исключений"""
    try:
        return await get_matrix(url)
    except Exception as e:
        print(f"Ошибка при получении матрицы: {e}")
        return []

async def main():
    url = "https://raw.githubusercontent.com/avito-tech/python-trainee-assignment/main/matrix.txt"
    try:
        result = await get_matrix(url)
        print(f"Результат обхода: {result}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    asyncio.run(main())